import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { CreateCollectionDialog } from "@/components/data-library/create-collection-dialog";
import { CollectionCard } from "@/components/data-library/collection-card";
import { IconDatabase } from "@tabler/icons-react";

// Force dynamic rendering to avoid database connection during build
export const dynamic = "force-dynamic";

export default async function DataLibraryPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");

  const org = await prisma.organization.findUnique({
    where: { slug },
  });

  if (!org) redirect("/select-organization");

  // Fetch collections for this organization
  const collections = await prisma.collection.findMany({
    where: {
      organizationId: org.id,
    },
    include: {
      _count: {
        select: {
          files: true,
        },
      },
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  return (
    <div className="flex flex-1 flex-col gap-4 p-4 md:gap-6 md:p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Library</h1>
          <p className="text-muted-foreground">
            Manage your document collections and files for RAG processing
          </p>
        </div>
        <CreateCollectionDialog />
      </div>

      {collections.length === 0 ? (
        <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed shadow-sm">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="rounded-full bg-muted p-4">
              <IconDatabase className="h-10 w-10 text-muted-foreground" />
            </div>
            <div className="max-w-md">
              <h3 className="text-lg font-semibold">No collections yet</h3>
              <p className="text-sm text-muted-foreground mt-2">
                Get started by creating your first collection to organize your
                files.
              </p>
            </div>
            <CreateCollectionDialog />
          </div>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {collections.map((collection: any) => (
            <CollectionCard
              key={collection.id}
              collection={collection}
              orgSlug={slug}
            />
          ))}
        </div>
      )}
    </div>
  );
}
