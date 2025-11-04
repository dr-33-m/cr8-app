import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";
import { AssetSearchInputProps } from "@/lib/types/assetBrowser";

export function AssetSearchInput({
  value,
  onChange,
  onClear,
  placeholder = "Search assets...",
  className = "",
  compact = false,
}: AssetSearchInputProps) {
  return (
    <div className={`relative ${className}`}>
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
      <Input
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`pl-10 ${compact ? "" : "w-64"}`}
      />
      {value && (
        <Button
          variant="destructive"
          size="icon"
          className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8"
          onClick={onClear}
        >
          <X className="w-4 h-4" />
        </Button>
      )}
    </div>
  );
}
