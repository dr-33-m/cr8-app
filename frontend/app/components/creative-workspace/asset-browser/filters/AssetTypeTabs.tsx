import { AssetType, AssetTypeTabsProps } from "@/lib/types/assetBrowser";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function AssetTypeTabs({
  selectedType,
  onTypeChange,
  className = "",
}: AssetTypeTabsProps) {
  return (
    <Tabs
      value={selectedType}
      onValueChange={(value) => onTypeChange(value as AssetType)}
      className={className}
    >
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="hdris">HDRIs</TabsTrigger>
        <TabsTrigger value="textures">Textures</TabsTrigger>
        <TabsTrigger value="models">Models</TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
