import imaplib
import email
import re
import time
from datetime import datetime, timedelta
from email.utils import parseaddr


# =============================
# Helpers IMAP
# =============================
def _imap_connect(usuario: str, senha: str):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(usuario, senha)
    mail.select("inbox")
    return mail


def _imap_search_ids(mail, criteria: str):
    status, data = mail.search(None, criteria)
    if status != "OK":
        return []
    raw = data[0]
    if not raw:
        return []
    return raw.split()


def _fetch_text_body(mail, msg_id: bytes) -> str:
    """
    Busca o corpo do e-mail como texto (prioriza text/plain).
    """
    status, data = mail.fetch(msg_id, "(RFC822)")
    if status != "OK" or not data or not data[0]:
        return ""

    msg = email.message_from_bytes(data[0][1])

    # Multipart: procura text/plain
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                try:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                except Exception:
                    return payload.decode("utf-8", errors="replace")
        return ""

    payload = msg.get_payload(decode=True) or b""
    try:
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    except Exception:
        return payload.decode("utf-8", errors="replace")


def _from_matches(msg_from: str, expected_email: str) -> bool:
    """
    Compara remetente de forma robusta.
    """
    _, addr = parseaddr(msg_from or "")
    if addr:
        return addr.lower() == expected_email.lower()
    return expected_email.lower() in (msg_from or "").lower()


def _today_imap_str() -> str:
    # IMAP usa "14-Jan-2026"
    return datetime.now().strftime("%d-%b-%Y")


def _yesterday_imap_str() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")


# =============================
# SENHA DO DIA (Vetor)
# =============================
def buscar_senha_gmail(usuario: str, senha: str):
    """
    Retorna (senha, erro). Não interage com UI.
    """
    remetente = "noreply@vetorsolucoes.com.br"

    # Mais robusto que ON hoje: SINCE ontem + FROM
    criteria = f'(SINCE "{_yesterday_imap_str()}" FROM "{remetente}")'

    try:
        mail = _imap_connect(usuario, senha)
    except Exception as e:
        return None, f"Erro ao conectar ao servidor IMAP: {e}"

    try:
        ids = _imap_search_ids(mail, criteria)
        if not ids:
            return None, "Nenhum e-mail do remetente encontrado desde ontem."

        # Pega do mais recente para o mais antigo
        for msg_id in reversed(ids):
            status, head_data = mail.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
            if status != "OK":
                continue

            # Busca o email completo só se necessário
            status2, full_data = mail.fetch(msg_id, "(RFC822)")
            if status2 != "OK" or not full_data or not full_data[0]:
                continue

            msg = email.message_from_bytes(full_data[0][1])
            if not _from_matches(msg.get("From", ""), remetente):
                continue

            corpo = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True) or b""
                        corpo = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                        break
            else:
                payload = msg.get_payload(decode=True) or b""
                corpo = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

            # Regex mais tolerante
            m = re.search(r"\bsua senha.*?:\s*([a-zA-Z0-9]+)", corpo, re.IGNORECASE)
            if m:
                return m.group(1), None

        return None, "E-mail encontrado, mas não foi possível extrair a senha."
    except Exception as e:
        return None, f"Erro durante a busca: {e}"
    finally:
        try:
            mail.close()
            mail.logout()
        except Exception:
            pass


# =============================
# TOKEN GETCARD
# =============================
def buscar_token_getcard(usuario: str, senha: str, max_tentativas: int = 4, intervalo_seg: int = 5):
    """
    Retorna (token, erro). Reusa a mesma conexão IMAP.
    Marca como \Seen quando captura.
    """
    remetente = "liberacaotef@getcard.com.br"
    criteria = f'(UNSEEN SINCE "{_yesterday_imap_str()}" FROM "{remetente}")'
    regex = re.compile(r"Seu token para autenticar seu login:\s*(\d+)", re.IGNORECASE)

    try:
        mail = _imap_connect(usuario, senha)
    except Exception as e:
        return None, f"Erro ao conectar ao servidor IMAP: {e}"

    try:
        for tentativa in range(max_tentativas):
            if tentativa > 0:
                time.sleep(intervalo_seg)

            ids = _imap_search_ids(mail, criteria)
            if not ids:
                continue

            for msg_id in reversed(ids):
                body = _fetch_text_body(mail, msg_id)
                if not body:
                    continue

                m = regex.search(body)
                if m:
                    try:
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                    except Exception:
                        pass
                    return m.group(1), None

        return None, "Token não encontrado após as tentativas."
    except Exception as e:
        return None, f"Erro durante a busca do token: {e}"
    finally:
        try:
            mail.close()
            mail.logout()
        except Exception:
            pass


# =============================
# TOKEN FISERV
# =============================
def buscar_token_fiserv(usuario: str, senha: str, max_tentativas: int = 4, intervalo_seg: int = 5):
    """
    Retorna (token, erro). Reusa a mesma conexão IMAP.
    Marca como \Seen quando captura.
    """
    remetente = "noreply@fiserv.com"
    criteria = f'(UNSEEN SINCE "{_yesterday_imap_str()}" FROM "{remetente}")'
    regex = re.compile(r"Código:\s*(\d+)", re.IGNORECASE)

    try:
        mail = _imap_connect(usuario, senha)
    except Exception as e:
        return None, f"Erro ao conectar ao servidor IMAP: {e}"

    try:
        for tentativa in range(max_tentativas):
            if tentativa > 0:
                time.sleep(intervalo_seg)

            ids = _imap_search_ids(mail, criteria)
            if not ids:
                continue

            for msg_id in reversed(ids):
                body = _fetch_text_body(mail, msg_id)
                if not body:
                    continue

                m = regex.search(body)
                if m:
                    try:
                        mail.store(msg_id, "+FLAGS", "\\Seen")
                    except Exception:
                        pass
                    return m.group(1), None

        return None, "Token Fiserv não encontrado após as tentativas."
    except Exception as e:
        return None, f"Erro durante a busca do token Fiserv: {e}"
    finally:
        try:
            mail.close()
            mail.logout()
        except Exception:
            pass
