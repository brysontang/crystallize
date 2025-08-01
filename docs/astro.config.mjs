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
          label: 'The Crystallize CLI',
          items: [
            { label: 'Tutorial: Your First CLI Experiment', slug: 'cli/tutorial-cli-workflow' },
            { label: 'How-To: Configure Experiments (config.yaml)', slug: 'cli/how-to-configure' },
            { label: 'Putting It All Together - Building a Graph Experiment', slug: 'cli/tutorial-graph-experiment' },
          ],
        },
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
            {
              label: 'Saving Artifacts',
              slug: 'how-to/artifacts',
            },
            {
              label: 'Creating Custom Plugins',
              slug: 'how-to/creating-plugins',
            },
            {
              label: 'Chaining Experiments with a DAG',
              slug: 'how-to/dag-experiments',
            },
            {
              label: 'Advanced DAG Caching & Execution',
              slug: 'how-to/advanced-dag-strategies',
            },
            {
              label: 'Viewing Provenance',
              slug: 'how-to/view-provenance',
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
            {
              label: 'Parameter Optimization',
              slug: 'tutorials/optimization',
            },
            {
              label: 'The Full Workflow',
              slug: 'tutorials/full-workflow',
            },
          ],
        },
        {
          label: 'Explanation',
          items: [
            {
              label: 'Core Concepts',
              slug: 'explanation/core-concepts',
            },
            {
              label: 'Reproducibility',
              slug: 'explanation/reproducibility',
            },
            {
              label: 'Parallel Execution Strategies',
              slug: 'explanation/parallelism',
            },
            {
              label: 'Extending Crystallize',
              slug: 'explanation/extending',
            },
            {
              label: 'Design Patterns & Best Practices',
              slug: 'explanation/best-practices',
            },
            {
              label: 'How Crystallize Compares to Other Tools',
              slug: 'explanation/comparisons',
            },
            {
              label: 'Frequently Asked Questions',
              slug: 'explanation/faq',
            },
          ],
        },
        {
          label: 'API Reference',
          autogenerate: { directory: 'reference' },
        },
        {
          label: 'Extras',
          items: [
            { label: 'RayExecution', slug: 'extras/ray' },
            { label: 'vLLM Engine', slug: 'extras/vllm' },
            { label: 'Ollama Client', slug: 'extras/ollama' },
            { label: 'OpenAI Client', slug: 'extras/openai' },
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
