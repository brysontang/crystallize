// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import catppuccin from '@catppuccin/starlight';
import starlightClientMermaid from '@pasqal-io/starlight-client-mermaid';

// https://astro.build/config
export default defineConfig({
  site: 'https://brysontang.github.io',
  base: '/crystallize/',
  integrations: [
    starlight({
      title: 'My Docs',
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/withastro/starlight',
        },
      ],
      sidebar: [
        {
          label: 'How-to Guides',
          items: [
            {
              label: 'Creating Custom Pipeline Steps',
              slug: 'how-to/custom-steps',
            },
            {
              label: 'Customizing Experiments',
              slug: 'how-to/customizing-experiments',
            },
            {
              label: 'Integrating Statistical Tests',
              slug: 'how-to/integrate-stats',
            },
          ],
        },
        {
          label: 'Tutorials',
          items: [
            {
              label: 'Getting Started',
              slug: 'tutorials/intro',
            },
            {
              label: 'Building Your First Experiment',
              slug: 'tutorials/basic-experiment',
            },
            { label: 'Adding Treatments', slug: 'tutorials/adding-treatments' },
            {
              label: 'Verifying Hypotheses',
              slug: 'tutorials/hypotheses',
            },
            {
              label: 'Scaling with Replicates and Parallelism',
              slug: 'tutorials/parallelism',
            },
          ],
        },
        {
          label: 'Glossary',
          slug: 'glossary',
        },
        {
          label: 'Contributing',
          slug: 'contributing',
        },
      ],
      plugins: [
        catppuccin({
          dark: { flavor: 'frappe', accent: 'sky' },
          light: { flavor: 'latte', accent: 'sky' },
        }),
        starlightClientMermaid({
          // optional tweaks
          className: 'mermaid', // wrapper class for styling
          loadingPlaceholder: '⏳', // shown while SVG renders
        }),
      ],
    }),
  ],
});
