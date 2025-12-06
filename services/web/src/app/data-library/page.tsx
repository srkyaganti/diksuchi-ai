import { redirect } from "next/navigation";

export default function DataLibraryPage() {
  redirect("/select-organization?redirect=data-library");
}
