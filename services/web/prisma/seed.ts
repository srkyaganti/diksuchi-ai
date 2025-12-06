import { config } from "dotenv";
import { PrismaClient } from "../src/generated/prisma/client";

// Load environment variables from .env files
config({ path: ".env" });
config({ path: ".env.local", override: true });

const prisma = new PrismaClient();

async function main() {
  const email = process.env.SUPER_ADMIN_EMAIL || "admin@example.com";
  const password = process.env.SUPER_ADMIN_PASSWORD || "Admin123!";
  const name = "Super Administrator";

  // Check if super admin already exists
  const existing = await prisma.user.findUnique({
    where: { email },
  });

  if (existing) {
    console.log("Super admin already exists");
    return;
  }

  // Use Better Auth's API to create user with properly hashed password
  const response = await fetch(`${process.env.BETTER_AUTH_URL || "http://localhost:3000"}/api/auth/sign-up/email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create user: ${await response.text()}`);
  }

  const result = await response.json();

  // Update user to be super admin
  await prisma.user.update({
    where: { email },
    data: {
      isSuperAdmin: true,
      emailVerified: true,
      mustChangePassword: false,
    },
  });

  console.log("Super admin created:", {
    email,
    password: "Use the password you provided",
  });
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
