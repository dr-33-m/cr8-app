# Animation System Usage Guide

This document provides a comprehensive guide on how to use the Animation System in the Cr8 application. It covers how to select and apply animations, as well as how to create new animations.

## Accessing Animation Controls

The Animation System is integrated into the Scene Controls panel in the Cr8 application. To access the animation controls:

1. Open a project in the Cr8 application
2. Locate the Scene Controls panel on the left side of the screen
3. Click on the "Animations" section to expand it

## Selecting and Applying Animations

### Using the Animation Selectors

The Animation System provides three animation selectors, one for each animation type:

1. **Camera Animation Selector**: For selecting and applying camera animations
2. **Light Animation Selector**: For selecting and applying light animations
3. **Product Animation Selector**: For selecting and applying product animations

To select and apply an animation:

1. Choose the appropriate animation selector based on the type of animation you want to apply
2. Click on the dropdown to see available animations
3. Select an animation from the list
4. Click the "Apply" button to apply the animation to the scene

### Using the Animation Panel

For a more detailed view of available animations, you can use the Animation Panel:

1. Click on the "Animations" section in the Scene Controls panel
2. The Animation Panel will display tabs for Camera, Light, and Product animations
3. Select a tab to view animations of that type
4. Browse through the available animations
5. Click the "Apply" button on an animation card to apply it to the scene

## Animation Types

### Camera Animations

Camera animations control the movement, rotation, and focus of the camera in the scene. Examples include:

- **Orbit**: The camera orbits around a focal point
- **Dolly**: The camera moves forward or backward
- **Pan**: The camera moves horizontally
- **Tilt**: The camera rotates up or down
- **Zoom**: The camera's field of view changes

### Light Animations

Light animations control the properties of lights in the scene. Examples include:

- **Pulse**: The light intensity pulses up and down
- **Color Shift**: The light color changes over time
- **Flicker**: The light intensity varies randomly
- **Rotate**: The light rotates around a point
- **Fade**: The light fades in or out

### Product Animations

Product animations control the movement and properties of 3D objects in the scene. Examples include:

- **Rotate**: The object rotates around an axis
- **Scale**: The object scales up or down
- **Move**: The object moves along a path
- **Bounce**: The object bounces up and down
- **Shake**: The object shakes or vibrates

## Connection Status

The Animation System requires a WebSocket connection to the backend to apply animations. The connection status is displayed in the Animation Panel:

- **Connected**: Animations can be applied
- **Connecting**: The system is attempting to establish a connection
- **Disconnected**: The connection has been lost
- **Failed**: The connection could not be established

If the connection is not established, you will see a warning message in the Animation Panel. You will need to wait for the connection to be established before you can apply animations.

## Creating New Animations

### Prerequisites

To create new animations, you need:

1. Access to the Blender file for the template
2. Basic knowledge of Blender animation tools
3. Understanding of the animation data format

### Creating a Camera Animation

To create a new camera animation:

1. Open the template in Blender
2. Select the camera object
3. Create keyframes for the camera's location, rotation, and other properties
4. Export the animation data using the template export tool
5. Import the animation data into the Cr8 database

### Creating a Light Animation

To create a new light animation:

1. Open the template in Blender
2. Select the light object
3. Create keyframes for the light's intensity, color, and other properties
4. Export the animation data using the template export tool
5. Import the animation data into the Cr8 database

### Creating a Product Animation

To create a new product animation:

1. Open the template in Blender
2. Select the product object
3. Create keyframes for the object's location, rotation, scale, and other properties
4. Export the animation data using the template export tool
5. Import the animation data into the Cr8 database

## Animation Data Format

Animations are stored in a JSON format with the following structure:

```json
{
  "id": "unique_animation_id",
  "name": "Animation Name",
  "template_type": "camera|light|product_animation",
  "templateData": {
    "keyframes": [
      {
        "frame": 0,
        "properties": {
          "location": [0, 0, 0],
          "rotation": [0, 0, 0],
          "scale": [1, 1, 1]
        }
      },
      {
        "frame": 10,
        "properties": {
          "location": [1, 0, 0],
          "rotation": [0, 0, 0],
          "scale": [1, 1, 1]
        }
      }
    ],
    "duration": 5.0,
    "easing": "ease-in-out"
  },
  "is_public": true,
  "created_at": "2025-03-04T12:00:00Z",
  "updated_at": "2025-03-04T12:00:00Z",
  "creator_id": "user_id"
}
```

## Troubleshooting

### Animation Not Applying

If an animation is not applying to the scene, check the following:

1. **WebSocket Connection**: Ensure that the WebSocket connection is established
2. **Target Empty**: Make sure the target empty exists in the scene
3. **Animation Data**: Verify that the animation data is valid
4. **Console Errors**: Check the browser console for any error messages

### Animation Looks Incorrect

If an animation is applying but looks incorrect, check the following:

1. **Animation Data**: Verify that the animation data is correct
2. **Target Empty**: Make sure the animation is being applied to the correct target
3. **Scene Setup**: Ensure that the scene is set up correctly for the animation

### WebSocket Connection Issues

If you are experiencing WebSocket connection issues, try the following:

1. **Refresh the Page**: Refresh the page to attempt to re-establish the connection
2. **Check Server Status**: Ensure that the backend server is running
3. **Network Issues**: Check for any network issues that might be preventing the connection
4. **Firewall Settings**: Ensure that your firewall is not blocking WebSocket connections

## Best Practices

### Animation Selection

- Choose animations that complement the scene and product
- Avoid animations that distract from the main focus of the scene
- Use subtle animations for a professional look

### Animation Timing

- Keep animations short and to the point
- Use appropriate timing for the type of animation
- Consider the overall flow of the scene when selecting animation timing

### Animation Combinations

- Combine animations thoughtfully to create a cohesive scene
- Avoid conflicting animations that might cancel each other out
- Consider how different animations will interact with each other

## Conclusion

The Animation System provides a powerful way to add dynamic elements to your 3D scenes. By following this guide, you should be able to effectively select, apply, and create animations for your projects.

For more detailed information about the Animation System, refer to the following documentation:

- [Architecture](./architecture.md): Detailed system architecture and data flow
- [Backend Implementation](./implementation/backend.md): Details of the backend implementation
- [Frontend Implementation](./implementation/frontend.md): Details of the frontend components
- [WebSocket Communication](./implementation/websocket.md): Details of the WebSocket protocol
