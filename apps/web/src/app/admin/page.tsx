"use client";

import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/layout/RequireAuth";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";
import type { AdminOverview, AdminUserRow } from "@/lib/types";

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <Card className="text-center">
      <div className="font-display text-3xl font-semibold">{value}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-[color:var(--fg-muted)]">{label}</div>
    </Card>
  );
}

function AdminPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [users, setUsers] = useState<AdminUserRow[]>([]);

  useEffect(() => {
    void api.get<AdminOverview>("/api/v1/admin/overview").then(setOverview);
    void api.get<AdminUserRow[]>("/api/v1/admin/users").then(setUsers);
  }, []);

  async function toggleActive(user: AdminUserRow) {
    await api.patch(`/api/v1/admin/users/${user.id}`, { is_active: !user.is_active });
    setUsers(await api.get<AdminUserRow[]>("/api/v1/admin/users"));
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <h1 className="font-display text-2xl font-semibold">Admin Dashboard</h1>

      {overview && (
        <div className="grid grid-cols-3 gap-4 md:grid-cols-6">
          <StatTile label="Users" value={overview.total_users} />
          <StatTile label="Active (7d)" value={overview.active_users_7d} />
          <StatTile label="Conversations" value={overview.total_conversations} />
          <StatTile label="Messages" value={overview.total_messages} />
          <StatTile label="Books" value={overview.total_books} />
          <StatTile label="Qur'an plans" value={overview.total_quran_plans} />
        </div>
      )}

      <Card>
        <h2 className="mb-3 font-display text-lg font-semibold">Users</h2>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs uppercase tracking-wide text-[color:var(--fg-muted)]">
              <th className="pb-2">Name</th>
              <th className="pb-2">Email</th>
              <th className="pb-2">Role</th>
              <th className="pb-2">Status</th>
              <th className="pb-2" />
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} className="border-t border-[color:var(--hairline)]">
                <td className="py-2">{user.display_name}</td>
                <td className="py-2 text-[color:var(--fg-muted)]">{user.email}</td>
                <td className="py-2">{user.role}</td>
                <td className="py-2">{user.is_active ? "Active" : "Disabled"}</td>
                <td className="py-2 text-right">
                  <button
                    onClick={() => toggleActive(user)}
                    className="text-xs font-medium text-brass hover:underline"
                  >
                    {user.is_active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

export default function Page() {
  return (
    <RequireAuth>
      <AdminPage />
    </RequireAuth>
  );
}
