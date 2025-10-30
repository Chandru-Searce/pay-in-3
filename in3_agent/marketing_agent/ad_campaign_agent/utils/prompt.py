TEXT_REMOVER_PROMPT = """
{
  "task": "Modify the provided image by removing only the specified text components while preserving all other visual elements.",
  "instructions": {
    "1. Text Components to Remove": {
      "headline_text": "Completely erase the headline text from the image.",
      "cta_button_text": "Remove all text within the CTA button.",
      "underline": "Eliminate any underline associated with the headline or other text elements."
    },
    "2. Elements to Preserve": {
      "cta_button_shape": "Retain the exact shape, outline, and structure of the CTA button without any modifications.",
      "cta_button_arrow": "Keep the arrow within the CTA button unchanged in size, position, color, and design.",
      "background": "Preserve the entire background, including colors, gradients, textures, and patterns, ensuring no alterations outside the text removal areas.",
      "icons": "Maintain all icons in their original form, including their size, color, position, and design.",
      "logos": "Keep all logos intact with no changes to their appearance, placement, or details.",
      "shapes_and_patterns": "Retain all decorative shapes, patterns, or design elements exactly as they appear in the original image.",
      "colors_and_visual_elements": "Preserve all colors, shadows, highlights, and other visual effects throughout the image, ensuring no unintended changes."
    },
    "3. Blending and Seamlessness": {
      "blending_instruction": "After removing the headline text, CTA button text, and underline, seamlessly blend the affected areas with the surrounding background and button textures.",
      "color_matching": "Match the colors, gradients, and textures of the adjacent areas to ensure a natural, cohesive appearance that aligns with the original design.",
      "visual_integrity": "Avoid any visible patches, distortions, or mismatches in the edited areas."
    },
    "4. Additional Instructions": {
      "element_modification": "Do not add, modify, or remove any non-text elements unless explicitly mentioned.",
      "aesthetic_consistency": "Ensure the overall aesthetic, style, and composition of the image remain consistent with the original after text removal.",
      "artifact_check": "Verify that no residual text artifacts or outlines remain in the edited areas."
    }
  },
  "goal": "Produce a clean, text-free version of the original image while maintaining complete visual fidelity and consistency across all preserved elements."
}

"""