#version 330 core
layout(location = 0) in vec2 vertexPosition_modelspace; // Vertices of the quad
out vec2 screenCoord; // Will pass screen-space equivalent to fragment shader

void main(){
    gl_Position = vec4(vertexPosition_modelspace, 0.0, 1.0);
    // Convert from clip space (-1 to 1) to texture/screen coordinate space (0 to 1)
    // This is often more convenient for fractal calculations in the fragment shader.
    screenCoord = (vertexPosition_modelspace + 1.0) / 2.0; 
}