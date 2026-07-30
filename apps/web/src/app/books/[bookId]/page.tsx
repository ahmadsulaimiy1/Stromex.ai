"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { RequireAuth } from "@/components/layout/RequireAuth";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import type { BookWithChapters, ChapterRead } from "@/lib/types";

function ChapterEditor({ bookId, chapter, onSaved }: { bookId: string; chapter: ChapterRead; onSaved: () => void }) {
  const [title, setTitle] = useState(chapter.title);
  const [content, setContent] = useState(chapter.content_markdown);
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await api.patch(`/api/v1/books/${bookId}/chapters/${chapter.id}`, {
        title,
        content_markdown: content,
      });
      onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-[color:var(--hairline)] p-4">
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="font-display text-lg font-semibold bg-transparent focus:outline-none"
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={10}
        className="resize-y rounded-md border border-[color:var(--hairline)] bg-transparent p-3 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-brass/40"
      />
      <Button variant="secondary" onClick={save} isLoading={saving} className="self-end">
        Save chapter
      </Button>
    </div>
  );
}

function BookDetailPage() {
  const params = useParams<{ bookId: string }>();
  const bookId = params.bookId;
  const [book, setBook] = useState<BookWithChapters | null>(null);

  async function loadBook() {
    setBook(await api.get<BookWithChapters>(`/api/v1/books/${bookId}`));
  }

  useEffect(() => {
    void loadBook();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  async function addChapter() {
    if (!book) return;
    await api.post(`/api/v1/books/${bookId}/chapters`, {
      title: `Chapter ${book.chapters.length + 1}`,
      order_index: book.chapters.length,
      content_markdown: "",
    });
    void loadBook();
  }

  function downloadPdf() {
    const token = window.localStorage.getItem("stromex.access_token");
    fetch(`${api.base}/api/v1/books/${bookId}/export.pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${book?.title ?? "book"}.pdf`;
        link.click();
        URL.revokeObjectURL(url);
      });
  }

  if (!book) {
    return <div className="p-6 text-sm text-[color:var(--fg-muted)]">Loading…</div>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">{book.title}</h1>
          <p className="text-sm text-[color:var(--fg-muted)]">{book.author_name}</p>
        </div>
        <Button onClick={downloadPdf}>Export PDF</Button>
      </div>

      <div className="flex flex-col gap-4">
        {book.chapters.map((chapter) => (
          <ChapterEditor key={chapter.id} bookId={bookId} chapter={chapter} onSaved={loadBook} />
        ))}
      </div>

      <Button variant="secondary" onClick={addChapter}>
        + Add chapter
      </Button>
    </div>
  );
}

export default function Page() {
  return (
    <RequireAuth>
      <BookDetailPage />
    </RequireAuth>
  );
}
