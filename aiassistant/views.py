from django.shortcuts import render

FAQ = [
    ("How to verify seller?", "Upload documents and check approval status. Always meet safely and verify originals."),
    ("What is 7/12?", "In Maharashtra, 7/12 extract shows land details, ownership, and cultivation info."),
]


def chat(request):
    answer = None
    q = ""
    if request.method == "POST":
        q = (request.POST.get("q") or "").strip()
        answer = "I can help with property search, docs checklist, and basic pricing. Ask a specific question."
        for k, v in FAQ:
            if k.lower() in q.lower():
                answer = v
                break
    return render(request, "aiassistant/chat.html", {"q": q, "answer": answer})
