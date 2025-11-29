import { PrismaClient } from "../src/generated/prisma/client";
import { hash } from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const email = process.env.SUPER_ADMIN_EMAIL || "admin@example.com";
  const password = process.env.SUPER_ADMIN_PASSWORD || "Admin123!";

  // Check if super admin already exists
  const existing = await prisma.user.findUnique({
    where: { email },
  });

  if (existing) {
    console.log("Super admin already exists");
    return;
  }

  // Hash password
  const hashedPassword = await hash(password, 10);

  // Create super admin
  const superAdmin = await prisma.user.create({
    data: {
      id: Math.random().toString(36).substring(7),
      email,
      name: "Super Administrator",
      emailVerified: true,
      isSuperAdmin: true,
      mustChangePassword: false,
      createdAt: new Date(),
      updatedAt: new Date(),
      accounts: {
        create: {
          id: Math.random().toString(36).substring(7),
          accountId: email,
          providerId: "credential",
          password: hashedPassword,
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      },
    },
  });

  console.log("Super admin created:", {
    email: superAdmin.email,
    id: superAdmin.id,
    password: "Use the password you provided via SUPER_ADMIN_PASSWORD env var",
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
