import { redirect } from "next/navigation";

export default function ChatPage() {
  redirect("/select-organization?redirect=chat");
}
