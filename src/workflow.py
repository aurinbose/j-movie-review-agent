# src/workflow.py
from src.agents import get_trending_movie, get_movie_details, generate_review
from src.hashnode_api import publish_to_hashnode
from src.prompt_logger import build_video_prompt, append_prompt_to_excel

def run_once_with_cli_approval():
    movie = get_trending_movie()
    if not movie:
        print("Could not find trending movie.")
        return

    print(f"Found movie: {movie['title']} - {movie['url']}")
    details = get_movie_details(movie["url"])
    review = generate_review(movie["title"], details["plot"])

    print("\n=== GENERATED REVIEW ===\n")
    print(review)
    print("\n========================\n")

    decision = input("Approve this review for publishing? (y/n): ").strip().lower()
    if decision != "y":
        print("Not publishing. You can manually edit/save it instead.")
        return

    result = publish_to_hashnode(movie["title"], review, publish=True)
    print("Publish result:", result)

    prompt = build_video_prompt(movie["title"], review)
    prompt_path = append_prompt_to_excel(prompt)
    print("\n📋 Video prompt generated:\n")
    print(prompt)
    print(f"\n💾 Prompt saved to: {prompt_path}")

def run_once_for_web_approval():
    movie = get_trending_movie()
    if not movie:
        print("Could not find trending movie.")
        return

    details = get_movie_details(movie["url"])
    review = generate_review(movie["title"], details["plot"])
    # Instead of saving for web approval, create a draft on Hashnode
    print("Creating draft on Hashnode (not publishing)...")
    result = publish_to_hashnode(movie["title"], review, publish=False)
    print("Draft result:", result)
    print("Review saved as draft. You can now review and publish manually on Hashnode.")

    prompt = build_video_prompt(movie["title"], review)
    prompt_path = append_prompt_to_excel(prompt)
    print("\n📋 Video prompt generated:\n")
    print(prompt)
    print(f"\n💾 Prompt saved to: {prompt_path}")

