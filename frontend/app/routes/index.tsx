import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PlusCircle, Palette } from "lucide-react";
import { useLogto } from "@logto/react";
import { SignIn } from "@/components/SignIn";
import { isBrowser } from "@/lib/utils";
import { CardGlass } from "@/components/ui/card-glass";
import { CreateProjectDialog } from "@/components/dashboard/CreateProjectDialogue";
import { CreateMoodboardDialog } from "@/components/moodboard/CreateMoodboardDIalogue";
import { useMediaQuery } from "react-responsive";
import { MobileMessage } from "@/components/MobileMessage";

export const Route = createFileRoute("/")({
  component: Home,
});

function Home() {
  const [activeTab, setActiveTab] = useState("create");
  const isMobile = useMediaQuery({ maxWidth: 768 });
  // FIXME: This is a temporary solution until we have a proper way to handle authentication in the Server.
  const logto = isBrowser ? useLogto() : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C] text-white">
      {logto?.isAuthenticated ? (
        <main className="container mx-auto px-4 pt-28 pb-8">
          <div className="max-w-5xl mx-auto">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-48 mx-auto grid-cols-2 bg-white/10 p-1">
                <TabsTrigger
                  value="create"
                  className="data-[state=active]:bg-[#0077B6] data-[state=active]:text-white"
                >
                  Create
                </TabsTrigger>
                <TabsTrigger
                  value="projects"
                  className="data-[state=active]:bg-[#FFD100] data-[state=active]:text-white"
                >
                  Projects
                </TabsTrigger>
              </TabsList>

              <TabsContent value="create" className="mt-12">
                <h2 className="text-2xl font-bold mb-8 text-center">
                  Create New Project
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-2xl mx-auto">
                  <CardGlass className="p-8 group hover:scale-[1.02] transition-transform duration-300 aspect-square">
                    <div className="flex flex-col items-center text-center justify-between h-full">
                      <div className="flex flex-col items-center">
                        <div className="mb-6 p-4 rounded-full bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
                          <PlusCircle className="w-8 h-8 text-blue-400" />
                        </div>
                        <h3 className="text-xl font-semibold mb-4">
                          New Project
                        </h3>
                        <p className="text-gray-400">
                          Create a new project with customized settings and
                          templates.
                        </p>
                      </div>
                      <CreateProjectDialog />
                    </div>
                  </CardGlass>

                  <CardGlass className="p-8 group hover:scale-[1.02] transition-transform duration-300 aspect-square">
                    <div className="flex flex-col items-center text-center justify-between h-full">
                      <div className="flex flex-col items-center">
                        <div className="mb-6 p-4 rounded-full bg-purple-500/10 group-hover:bg-purple-500/20 transition-colors">
                          <Palette className="w-8 h-8 text-purple-400" />
                        </div>
                        <h3 className="text-xl font-semibold mb-4">
                          New Moodboard
                        </h3>
                        <p className="text-gray-400">
                          Create a new moodboard to collect and organize your
                          inspiration.
                        </p>
                      </div>
                      <CreateMoodboardDialog />
                    </div>
                  </CardGlass>
                </div>
              </TabsContent>

              <TabsContent value="projects" className="mt-12">
                <h2 className="text-2xl font-bold mb-8 text-center">
                  My Projects
                </h2>
                {/* Add projects content here */}
              </TabsContent>
            </Tabs>
          </div>
        </main>
      ) : isMobile ? (
        <MobileMessage />
      ) : (
        <SignIn />
      )}
    </div>
  );
}
