## Brief overview

Guidelines for UI component styling and responsive design in the cr8-app project. These rules ensure consistent use of the design system, proper component composition, and responsive layouts.

## Theme consistency

- Always use theme variables from the design system (bg-primary, bg-secondary, bg-muted, border-border, text-primary, etc.)
- Avoid hardcoding colors, shadows, or spacing values
- Use theme color variants with opacity (bg-primary/30, bg-secondary/20, border-primary/30)
- Leverage existing theme tokens for hover states, focus states, and interactive elements

## Component composition

- Prefer shadcn/ui Card components over custom div containers for consistent styling
- Use Card, CardHeader, CardContent, CardFooter structure when appropriate
- Remove redundant styling when using Card components (backdrop-blur, bg-white/x, rounded-lg, border-white/x)
- Keep Card components clean and let the design system handle base styling

## Layout vs styling separation

- Apply layout styling (flex, grid, positioning) at page/container level
- Keep components focused on their specific styling and behavior
- Avoid mixing layout concerns with component styling
- Use utility classes for spacing, alignment, and responsive behavior

## Responsive design principles

- Use responsive prefixes (sm:, md:, lg:, xl:) for breakpoint-specific styling
- Ensure components work well across different screen sizes
- Test dialog and modal widths for content overflow issues
- Use appropriate max-width classes (max-w-full, max-w-7xl, max-w-6xl) based on content needs

## Interactive states

- Use theme-based hover states (hover:bg-primary/30, hover:bg-secondary/20)
- Apply consistent focus states using theme variables
- Ensure sufficient contrast for interactive elements
- Use primary color for active/selected states

## Component width and spacing

- Adjust component widths based on content requirements (w-80 → w-96 for better content display)
- Use appropriate dialog widths to prevent content overlap (max-w-full for complex content)
- Maintain consistent padding and margins using theme spacing scale
- Test component widths with real content to avoid cramping

## Color and contrast

- Use secondary colors for backgrounds and subtle elements (bg-secondary/30)
- Apply primary colors for interactive and important elements
- Ensure adequate contrast ratios for accessibility
- Use muted colors for secondary text and less prominent elements

## Shadow and depth

- Use subtle shadows for depth (shadow-sm, shadow-md)
- Apply shadows consistently across similar components
- Avoid heavy shadows that conflict with the design system
- Use theme-appropriate shadow colors and opacity levels
