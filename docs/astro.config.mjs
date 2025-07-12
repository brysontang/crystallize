// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import catppuccin from '@catppuccin/starlight';
import starlightClientMermaid from '@pasqal-io/starlight-client-mermaid';

// https://astro.build/config
export default defineConfig({
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
        // {
        //   label: 'Tutorials',
        //   items: [
        //     {
        //       label: 'Your First Experiment',
        //       slug: 'tutorials/first-experiment',
        //     },
        //     { label: 'Real-World CSV Example', slug: 'tutorials/csv-example' },
        //     {
        //       label: 'Advanced Scientific Experimentation',
        //       slug: 'tutorials/scientific-experimentation',
        //     },
        //   ],
        // },
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
