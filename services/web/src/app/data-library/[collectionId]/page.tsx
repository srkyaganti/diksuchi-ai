import { redirect } from "next/navigation";
import Link from "next/link";
import prisma from "@/lib/prisma";
import { FileListTable } from "@/components/data-library/file-list-table";
import { FileUploadDialogWrapper } from "@/components/data-library/file-upload-dialog-wrapper";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { IconChevronRight } from "@tabler/icons-react";

// Force dynamic rendering to avoid database connection during build
export const dynamic = 'force-dynamic';

export default async function CollectionPage({
  params,
}: {
  params: Promise<{ collectionId: string }>;
}) {
  const { collectionId } = await params;

  // Fetch collection
  const collection = await prisma.collection.findUnique({
    where: {
      id: collectionId,
    },
    include: {
      _count: {
        select: {
          files: true,
        },
      },
    },
  });

  if (!collection) {
    redirect("/data-library");
  }

  // Fetch files for the collection
  const dbFiles = await prisma.file.findMany({
    where: {
      collectionId: collectionId,
    },
    orderBy: {
      uploadedAt: "desc",
    },
  });

  // Convert Date objects to ISO strings for the component
  const files = dbFiles.map((file) => ({
    ...file,
    uploadedAt: file.uploadedAt.toISOString(),
  }));

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/data-library">Data Library</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator>
            <IconChevronRight className="h-4 w-4" />
          </BreadcrumbSeparator>
          <BreadcrumbItem>
            <BreadcrumbPage>{collection.name}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{collection.name}</h1>
          {collection.description && (
            <p className="text-muted-foreground mt-2">{collection.description}</p>
          )}
          <p className="text-sm text-muted-foreground mt-1">
            {files.length} {files.length === 1 ? "file" : "files"}
          </p>
        </div>
        <FileUploadDialogWrapper collectionId={collectionId} />
      </div>

      <FileListTable files={files} />
    </div>
  );
}
