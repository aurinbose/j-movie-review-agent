# src/hashnode_api.py - ✅ FINAL: body (NOT bodyMarkdown)
import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import re
import json
import time

load_dotenv()

HN_PUBLICATION_ID = os.getenv("HN_PUBLICATION_ID")
HN_ACCESS_TOKEN = os.getenv("HN_ACCESS_TOKEN")

def publish_to_hashnode(movie_title: str, review_content: str, publish: bool = True) -> dict:
    """Create a draft and optionally publish it.

    Args:
        movie_title: Title used for the post.
        review_content: HTML or markdown content for the body.
        publish: If False, only create the draft and do not call publishDraft.
    """
    
    if not all([HN_PUBLICATION_ID, HN_ACCESS_TOKEN]):
        return {"status": "skipped", "reason": "Missing credentials"}
    
    body_html = _format_review_html(movie_title, review_content)  # HTML!
    
    url = "https://gql.hashnode.com"
    headers = {
        "Authorization": f"Bearer {HN_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # STEP 1: Create Draft - try multiple possible input field names because
    # the GraphQL schema can vary (body vs bodyMarkdown vs content, etc.).
    draft_query = """
    mutation createDraft($input: CreateDraftInput!) {
      createDraft(input: $input) {
        draft {
          id
        }
      }
    }
    """

    # Prefer the schema field Hashnode returned in your logs: 'contentMarkdown'.
    # Fallback to common alternatives if needed.
    candidate_fields = ["contentMarkdown", "body", "content", "bodyMarkdown"]

    draft_result = None
    draft_id = None
    last_response = None

    try:
        for field in candidate_fields:
            payload = {
                "query": draft_query,
                "variables": {
                    "input": {
                        "publicationId": HN_PUBLICATION_ID,
                        "title": movie_title,
                        field: body_html,
                    }
                }
            }

            resp = requests.post(url, headers=headers, json=payload)
            last_response = resp
            if resp.status_code != 200:
                continue

            draft_result = resp.json()
            draft_data = draft_result.get('data', {}).get('createDraft', {})
            draft_id = draft_data.get('draft', {}).get('id')
            if draft_id:
                used_field = field
                break

        if not draft_id:
            return {"status": "error", "message": "No draft ID returned", "last_response": (last_response.text if last_response is not None else None)}
        
        # If caller only wants a draft, return draft info now.
        if not publish:
            return {"status": "draft_created", "draft_id": draft_id, "field_used": used_field}

        # STEP 2: Publish
        time.sleep(2)  # Rate limit

        publish_query = """
        mutation publishDraft($input: PublishDraftInput!) {
          publishDraft(input: $input) {
            story {
              id
              title
              slug
              url
            }
          }
        }
        """

        publish_payload = {
            "query": publish_query,
            "variables": {
                "input": {"id": draft_id}
            }
        }

        publish_response = requests.post(url, headers=headers, json=publish_payload)
        if publish_response.status_code != 200:
            return {"status": "error", "code": publish_response.status_code, "body": publish_response.text}

        publish_result = publish_response.json()
        publish_data = publish_result.get('data', {}).get('publishDraft', {})
        story = publish_data.get('story', {})

        if story and story.get('id'):
            post_url = story.get('url') or f"https://flicktalkies.hashnode.dev/{story.get('slug', 'post')}"
            return {"status": "success", "draft_id": draft_id, "post_id": story.get('id'), "live_url": post_url}
        return {"status": "error", "message": "Publish returned no story", "response": publish_result}
            
    except Exception as e:
        print(f"💥 Error: {repr(e)}")
        return {"status": "error", "message": str(e)}

def _format_review_html(title: str, content: str) -> str:
    """Hashnode HTML (body field expects HTML)"""
    content = re.sub(r'``````', '', content)
    
    return f"""
<h1 style="color:#2c3e50;">🎬 {title}</h1>
<div style="font-size:18px;line-height:1.7;color:#333;max-width:800px;">
    {content}
</div>
<hr style="margin:40px 0;border:none;height:2px;background:#eee;">
<p style="color:#777;font-size:14px;text-align:center;">
    🤖 <strong>Movie Review Agent</strong><br>
    {datetime.now().strftime('%B %d, %Y')}
</p>
    """.strip()


def draft_exists(draft_id: str) -> bool:
    """Check whether a draft with the given id exists on Hashnode.

    Returns True if the draft appears present, False otherwise or on error.
    """
    if not HN_ACCESS_TOKEN or not draft_id:
        return False

    url = "https://gql.hashnode.com"
    headers = {
        "Authorization": f"Bearer {HN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    query = """
    query getDraft($id: ID!) {
      draft(id: $id) {
        id
      }
    }
    """

    try:
        resp = requests.post(url, headers=headers, json={"query": query, "variables": {"id": draft_id}})
        if resp.status_code != 200:
            return False
        j = resp.json()
        if j.get("data", {}).get("draft", {}).get("id"):
            return True
        return False
    except Exception:
        return False

if __name__ == "__main__":
    result = publish_to_hashnode("Test Movie Review", "Your AI-generated content here!")
    print("\n" + "="*70)
    print(json.dumps(result, indent=2))
    print("="*70)
