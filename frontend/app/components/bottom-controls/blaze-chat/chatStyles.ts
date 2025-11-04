// Styling for MentionsInput using theme variables
export const mentionsInputStyle = {
  control: {
    fontSize: 14,
    fontWeight: "normal",
    minHeight: 32,
    maxHeight: 120,
    width: "100%",
  },
  "&multiLine": {
    control: {
      fontFamily: "inherit",
      minHeight: 32,
      maxHeight: 100,
      width: "100%",
    },
    highlighter: {
      padding: 12,
      overflow: "hidden",
      width: "100%",
    },
    input: {
      padding: 0,
      border: "none",
      borderRadius: 0,
      backgroundColor: "transparent",
      color: "var(--foreground)",
      outline: "none",
      resize: "none" as const,
      overflowX: "hidden",
      overflowY: "auto",
      whiteSpace: "pre-wrap",
      wordBreak: "break-word",
      width: "100%",
      minHeight: 32,
      maxHeight: 100,
      boxShadow: "none",
      boxSizing: "border-box",
    },
  },
  suggestions: {
    list: {
      backgroundColor: "var(--popover)",
      border: "1px solid var(--border)",
      boxShadow: "0 20px 25px -5px rgb(0 0 0 / 0.3)",
      fontSize: 14,
      overflow: "auto",
      maxHeight: 256,
      padding: "8px 0",
      minWidth: 280,
      maxWidth: 400,
    },
    item: {
      padding: 0,
      borderBottom: "none",
      "&focused": {
        backgroundColor: "transparent",
      },
    },
  },
};

// Styling for inbox mentions (primary color)
export const inboxMentionStyle = {
  borderBottom: "2px solid var(--primary)",
};

export const sceneMentionStyle = {
  borderBottom: "2px solid var(--secondary)",
};
