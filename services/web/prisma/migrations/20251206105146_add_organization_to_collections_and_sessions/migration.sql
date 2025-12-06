/*
  Warnings:

  - Added the required column `organizationId` to the `chat_sessions` table without a default value. This is not possible if the table is not empty.
  - Added the required column `organizationId` to the `collections` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "chat_sessions" ADD COLUMN     "organizationId" TEXT NOT NULL;

-- AlterTable
ALTER TABLE "collections" ADD COLUMN     "organizationId" TEXT NOT NULL;

-- CreateIndex
CREATE INDEX "chat_sessions_organizationId_idx" ON "chat_sessions"("organizationId");

-- CreateIndex
CREATE INDEX "collections_organizationId_idx" ON "collections"("organizationId");

-- AddForeignKey
ALTER TABLE "collections" ADD CONSTRAINT "collections_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "chat_sessions" ADD CONSTRAINT "chat_sessions_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;
