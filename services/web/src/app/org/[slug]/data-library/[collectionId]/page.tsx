import { redirect } from "next/navigation";
import { headers } from "next/headers";
import Link from "next/link";
import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { FileUploadDialog } from "@/components/data-library/file-upload-dialog";
import { FileListTable } from "@/components/data-library/file-list-table";
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
export const dynamic = "force-dynamic";

export default async function CollectionPage({
  params,
}: {
  params: Promise<{ slug: string; collectionId: string }>;
}) {
  const { slug, collectionId } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");

  const org = await prisma.organization.findUnique({
    where: { slug },
  });

  if (!org) redirect("/select-organization");

  // Fetch collection and verify it belongs to this organization
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
    redirect(`/org/${slug}/data-library`);
  }

  // Verify collection belongs to this organization
  if (collection.organizationId !== org.id) {
    redirect(`/org/${slug}/data-library`);
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
              <Link href={`/org/${slug}/data-library`}>Data Library</Link>
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
          <h1 className="text-3xl font-bold tracking-tight">
            {collection.name}
          </h1>
          {collection.description && (
            <p className="text-muted-foreground mt-2">
              {collection.description}
            </p>
          )}
          <p className="text-sm text-muted-foreground mt-1">
            {files.length} {files.length === 1 ? "file" : "files"}
          </p>
        </div>
        <FileUploadDialog collectionId={collectionId} />
      </div>

      <FileListTable files={files} />
    </div>
  );
}
