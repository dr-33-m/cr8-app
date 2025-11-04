import { Card } from "@/components/ui/card";
import { FileStepProps } from "@/lib/types/onboarding";

export function FileStep({ blendFiles, onFileSelect }: FileStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xl font-semibold mb-2 text-foreground">
          Select Blend File
        </h3>
        <p className="text-muted-foreground text-sm">
          Choose a .blend file to open
        </p>
      </div>
      <div className="max-h-60 overflow-y-auto space-y-2">
        {blendFiles.map((file, index) => (
          <Card
            key={index}
            className="p-3 cursor-pointer hover:bg-accent transition-colors"
            onClick={() => onFileSelect(file)}
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-foreground">{file.filename}</p>
                <p className="text-xs text-muted-foreground truncate">
                  {file.full_path}
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
