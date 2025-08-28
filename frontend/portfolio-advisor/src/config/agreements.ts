export type AgreementMeta = {
  id: string; // keep numeric IDs to match current FastAPI backend ("1".."4")
  title: string;
  version: string; // "1.0" (UI will render as v1.0)
  required: boolean;
  pdfUrl: string; // can be .md for now; swap to .pdf later
  summary: string;
};

export const AGREEMENTS: AgreementMeta[] = [
  {
    id: "1",
    title: "Terms",
    version: "1.0",
    required: true,
    pdfUrl: "/legal/terms-v1.0.md",
    summary:
      "Educational simulation only; no investment advice; limitations of liability; arbitration.",
  },
  {
    id: "2",
    title: "Privacy",
    version: "1.0",
    required: true,
    pdfUrl: "/legal/privacy-v1.0.md",
    summary:
      "What we collect (email, quiz answers, simulated trades), how we use/share, retention, your rights.",
  },
  {
    id: "3",
    title: "Advisory",
    version: "1.0",
    required: true,
    pdfUrl: "/legal/advisory-v1.0.md",
    summary:
      "No advisory relationship in beta; hypothetical performance limitations; AI explanations only.",
  },
  {
    id: "4",
    title: "Esign",
    version: "1.0",
    required: true,
    pdfUrl: "/legal/esign-v1.0.md",
    summary:
      "Consent to electronic records/signatures; hardware/software requirements; withdrawal method.",
  },
];
