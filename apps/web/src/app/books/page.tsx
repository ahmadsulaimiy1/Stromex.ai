"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { RequireAuth } from "@/components/layout/RequireAuth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { api } from "@/lib/api";
import type { BookRead } from "@/lib/types";

function BooksPage() {
  const [books, setBooks] = useState<BookRead[]>([]);
  const [title, setTitle] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadBooks() {
    setBooks(await api.get<BookRead[]>("/api/v1/books"));
  }

  useEffect(() => {
    void loadBooks();
  }, []);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/api/v1/books", { title, author_name: authorName, language: "en" });
      setTitle("");
      setAuthorName("");
      await loadBooks();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-semibold">Book Writing Workspace</h1>

      <Card>
        <h2 className="mb-4 font-display text-lg font-semibold">Start a new book</h2>
        <form onSubmit={handleCreate} className="grid grid-cols-2 gap-3">
          <Input
            id="title"
            label="Title"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <Input
            id="authorName"
            label="Author name"
            required
            value={authorName}
            onChange={(e) => setAuthorName(e.target.value)}
          />
          <Button type="submit" isLoading={submitting} className="col-span-2">
            Create book
          </Button>
        </form>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        {books.map((book) => (
          <Link key={book.id} href={`/books/detail?id=${book.id}`}>
            <Card className="transition-colors hover:bg-[color:var(--bg)]">
              <h3 className="font-display text-base font-semibold">{book.title}</h3>
              <p className="text-sm text-[color:var(--fg-muted)]">{book.author_name}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <RequireAuth>
      <BooksPage />
    </RequireAuth>
  );
}
