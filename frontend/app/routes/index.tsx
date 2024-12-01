// app/routes/index.tsx
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Music, ShoppingBag, Shirt, Users } from "lucide-react";
import { ProjectCard } from "@/components/dashboard/ProjectCard";
import {
  FashionShowList,
  MusicList,
  ProductShowCaseList,
  SocialMediaList,
} from "@/lib/data";
import { useLogto } from "@logto/react";
import { SignIn } from "@/components/SignIn";

export const Route = createFileRoute("/")({
  component: Home,
});

function Home() {
  const [activeTab, setActiveTab] = useState("create");
  const logto = typeof window !== "undefined" ? useLogto() : null;
  // const { signOut, isAuthenticated } = useLogto();
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C] text-white">
      {logto?.isAuthenticated ? (
        <main className="container mx-auto px-4 pt-24 pb-8">
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-4 bg-white/10  p-1">
              <TabsTrigger
                value="create"
                className=" data-[state=active]:bg-[#0077B6] data-[state=active]:text-white"
              >
                Create
              </TabsTrigger>
              <TabsTrigger
                value="templates"
                className=" data-[state=active]:bg-[#5C0A98] data-[state=active]:text-white"
              >
                Templates
              </TabsTrigger>
              <TabsTrigger
                value="assets"
                className=" data-[state=active]:bg-[#FF006E] data-[state=active]:text-white"
              >
                Assets
              </TabsTrigger>
              <TabsTrigger
                value="projects"
                className=" data-[state=active]:bg-[#FFD100] data-[state=active]:text-white"
              >
                Projects
              </TabsTrigger>
            </TabsList>
            <TabsContent value="create" className="mt-6">
              <h2 className="text-2xl font-bold mb-4">Create New Project</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <ProjectCard
                  title="Music Video"
                  icon={<Music className="h-8 w-8" />}
                  color="#0077B6"
                  items={MusicList}
                />
                <ProjectCard
                  title="Product Showcase"
                  icon={<ShoppingBag className="h-8 w-8" />}
                  color="#5C0A98"
                  items={ProductShowCaseList}
                />
                <ProjectCard
                  title="Fashion Show"
                  icon={<Shirt className="h-8 w-8" />}
                  color="#FF006E"
                  items={FashionShowList}
                />
                <ProjectCard
                  title="Social Media Post"
                  icon={<Users className="h-8 w-8" />}
                  color="#FFD100"
                  items={SocialMediaList}
                />
              </div>
            </TabsContent>
            <TabsContent value="templates" className="mt-6">
              <h2 className="text-2xl font-bold mb-4">Templates</h2>
              {/* Add template content here */}
            </TabsContent>
            <TabsContent value="assets" className="mt-6">
              <h2 className="text-2xl font-bold mb-4">Assets</h2>
              {/* Add assets content here */}
            </TabsContent>
            <TabsContent value="projects" className="mt-6">
              <h2 className="text-2xl font-bold mb-4">My Projects</h2>
              {/* Add projects content here */}
            </TabsContent>
          </Tabs>
        </main>
      ) : (
        <SignIn />
      )}
    </div>
  );
}
