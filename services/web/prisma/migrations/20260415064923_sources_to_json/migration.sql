/*
  Warnings:

  - The `sources` column on the `chat_messages` table would be dropped and recreated. This will lead to data loss if there is data in the column.

*/
-- AlterTable
ALTER TABLE "chat_messages" DROP COLUMN "sources",
ADD COLUMN     "sources" JSONB;
