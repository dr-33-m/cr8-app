## Brief overview

Guidelines for building maintainable React components with proper separation of concerns and modular architecture.

## Component design principles

- Always break down large components into smaller, focused components
- Each component should have a single responsibility
- Keep components under 50-60 lines when possible
- Extract reusable UI patterns into separate components

## Separation of concerns

- Separate UI logic from business logic
- Keep state management in parent components, pass data down as props
- Extract event handlers and complex logic to parent components
- Components should focus on rendering and immediate user interactions

## Component organization

- Group related components in feature-specific directories
- Use index files for clean imports
- Follow consistent naming conventions (PascalCase for components)
- Create descriptive prop interfaces with clear types

## Layout vs component logic

- Apply layout styling at page/container level
- Keep components focused on their specific styling and behavior
- Avoid mixing layout concerns with component styling
- Use utility classes for spacing, alignment, and responsive behavior

## Button and action handling

- Keep action buttons in consistent locations (e.g., Controls section)
- Avoid scattering buttons throughout individual step components
- Maintain side-by-side button layouts for consistency
- Centralize button logic in parent components

## Props and interfaces

- Use descriptive prop names that clearly indicate purpose
- Provide callback props for user actions (onXxx pattern)
- Keep prop interfaces minimal and focused
- Use TypeScript for type safety and better developer experience

## File structure

- Create feature-specific directories (e.g., onboarding/local/)
- Use index.ts files for clean exports
- Keep related components together
- Follow existing project patterns and conventions
