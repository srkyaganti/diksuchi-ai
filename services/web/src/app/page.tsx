import { redirect } from "next/navigation";

export default function Home() {
  // Redirect to chat interface
  redirect("/chat");
}
