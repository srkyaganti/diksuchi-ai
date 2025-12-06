import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";

export default async function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Skip public routes and admin routes
  if (
    pathname.startsWith("/api/auth") ||
    pathname === "/login" ||
    pathname === "/change-password" ||
    pathname === "/" ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/public") ||
    pathname.startsWith("/admin")
  ) {
    return NextResponse.next();
  }

  // Redirect old routes to org selector
  if (pathname === "/chat" || pathname === "/data-library") {
    const redirect = pathname.substring(1); // Remove leading /
    return NextResponse.redirect(
      new URL(`/select-organization?redirect=${redirect}`, request.url)
    );
  }

  // Validate org routes
  if (pathname.startsWith("/org/")) {
    const session = await auth.api.getSession({ headers: request.headers });

    if (!session) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    // Extract org slug from path: /org/[slug]/...
    const parts = pathname.split("/");
    const orgSlug = parts[2];

    if (!orgSlug) {
      return NextResponse.redirect(
        new URL("/select-organization", request.url)
      );
    }

    // Membership verification is done in the layout for better error handling
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/org/:path*", "/chat", "/data-library", "/select-organization"],
};
