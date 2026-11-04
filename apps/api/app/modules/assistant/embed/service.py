from app.modules.assistant.models import Assistant
from app.modules.assistant.schemas import AssistantOut, EmbedCode


def build_assistant_out(assistant: Assistant, public_app_url: str) -> AssistantOut:
    base = public_app_url.rstrip("/")
    url = f"{base}/a/{assistant.public_token}"
    iframe = (
        f'<iframe src="{url}?embed=1" title="AI assistant" '
        'style="width:100%;max-width:420px;height:620px;border:1px solid #e5e7eb;border-radius:16px" '
        'loading="lazy"></iframe>'
    )
    script = (
        f'<script src="{base}/widget.js" data-assistant-token="{assistant.public_token}" '
        'data-title="Ask our assistant" defer></script>'
    )
    return AssistantOut(
        token=assistant.public_token,
        assistant_url=url,
        rotated_at=assistant.rotated_at,
        embed=EmbedCode(iframe=iframe, script=script),
    )
