// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import catppuccin from '@catppuccin/starlight';

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
        {
          label: 'Introduction',
          items: [
            { label: 'The Vision', slug: 'introduction/vision' },
            { label: 'Why Crystallize?', slug: 'introduction/why' },
            { label: 'Getting Started', slug: 'introduction/getting-started' },
          ],
        },
        {
          label: 'Installation & Getting Started',
          items: [
            {
              label: 'Installation Instructions',
              slug: 'installation/installation',
            },
            {
              label: 'Basic Usage & Quick Test',
              slug: 'installation/basic-usage',
            },
            {
              label: 'Common Issues & Troubleshooting',
              slug: 'installation/troubleshooting',
            },
            {
              label: 'Next Steps & Additional Resources',
              slug: 'installation/next-steps',
            },
          ],
        },
        {
          label: 'Core Concepts',
          items: [
            { label: 'Data Sources', slug: 'core-concepts/data-sources' },
            {
              label: 'Pipelines & Pipeline Steps',
              slug: 'core-concepts/pipelines',
            },
            {
              label: 'Immutable Context',
              slug: 'core-concepts/immutable-context',
            },
            {
              label: 'Treatments, Hypothesis & Statistical Validation',
              slug: 'core-concepts/treatments',
            },
            { label: 'Experiments', slug: 'core-concepts/experiments' },
          ],
        },
        {
          label: 'Tutorials',
          items: [
            {
              label: 'Your First Experiment',
              slug: 'tutorials/first-experiment',
            },
            { label: 'Real-World CSV Example', slug: 'tutorials/csv-example' },
            {
              label: 'Advanced Scientific Experimentation',
              slug: 'tutorials/scientific-experimentation',
            },
          ],
        },
        {
          label: 'Philosophy',
          items: [
            {
              label: 'Explicit Hypothesis-Driven Experimentation',
              slug: 'philosophy/hypothesis-driven',
            },
            {
              label: 'Minimalist Clarity & Extensibility',
              slug: 'philosophy/minimalist-clarity',
            },
            {
              label: 'Reproducibility as First-Class Citizen',
              slug: 'philosophy/reproducibility',
            },
            {
              label: 'Crystallize vs. Traditional Data Science Tools',
              slug: 'philosophy/crystallize-vs-traditional',
            },
          ],
        },
      ],
      plugins: [
        catppuccin({
          dark: { flavor: 'frappe', accent: 'sky' },
          light: { flavor: 'latte', accent: 'sky' },
        }),
      ],
    }),
  ],
});
