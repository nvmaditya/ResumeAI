/** Empty structured form matching backend defaults. */

export type FormSectionKey =
  | "experience"
  | "education"
  | "projects"
  | "skills";

export const DEFAULT_SECTION_ORDER: FormSectionKey[] = [
  "experience",
  "education",
  "projects",
  "skills",
];

export type ResumeForm = {
  basics: {
    name: string;
    email: string;
    phone: string;
    location: string;
    summary: string;
    website?: string;
    linkedin?: string;
    github?: string;
    links: { label: string; url: string }[];
  };
  experience: {
    company: string;
    position: string;
    dates: string;
    summary: string;
  }[];
  education: {
    institution: string;
    area: string;
    degree: string;
    dates: string;
  }[];
  projects: {
    name: string;
    description: string;
    url: string;
    highlights: string[];
  }[];
  skills: { name: string; keywords: string }[];
  /** Body section order (Basics/Summary always first). Affects Compile PDF. */
  section_order: FormSectionKey[];
};

export function emptyForm(): ResumeForm {
  return {
    basics: {
      name: "",
      email: "",
      phone: "",
      location: "",
      summary: "",
      website: "",
      linkedin: "",
      github: "",
      links: [],
    },
    experience: [],
    education: [],
    projects: [],
    skills: [],
    section_order: [...DEFAULT_SECTION_ORDER],
  };
}

function normalizeSectionOrder(raw: unknown): FormSectionKey[] {
  const allowed = new Set<FormSectionKey>(DEFAULT_SECTION_ORDER);
  const out: FormSectionKey[] = [];
  if (Array.isArray(raw)) {
    for (const x of raw) {
      let k = String(x || "")
        .trim()
        .toLowerCase();
      if (k === "work") k = "experience";
      if (allowed.has(k as FormSectionKey) && !out.includes(k as FormSectionKey)) {
        out.push(k as FormSectionKey);
      }
    }
  }
  for (const k of DEFAULT_SECTION_ORDER) {
    if (!out.includes(k)) out.push(k);
  }
  return out;
}

export function normalizeForm(raw: unknown): ResumeForm {
  const base = emptyForm();
  if (!raw || typeof raw !== "object") return base;
  const o = raw as Record<string, unknown>;
  const basics = (o.basics as Record<string, unknown>) || {};
  return {
    basics: {
      name: String(basics.name ?? ""),
      email: String(basics.email ?? ""),
      phone: String(basics.phone ?? ""),
      location: String(basics.location ?? ""),
      summary: String(basics.summary ?? ""),
      website: String(basics.website ?? ""),
      linkedin: String(basics.linkedin ?? ""),
      github: String(basics.github ?? ""),
      links: Array.isArray(basics.links)
        ? (basics.links as { label: string; url: string }[])
        : [],
    },
    experience: Array.isArray(o.experience)
      ? (o.experience as ResumeForm["experience"])
      : [],
    education: Array.isArray(o.education)
      ? (o.education as ResumeForm["education"])
      : [],
    projects: Array.isArray(o.projects)
      ? (o.projects as ResumeForm["projects"])
      : [],
    skills: Array.isArray(o.skills) ? (o.skills as ResumeForm["skills"]) : [],
    section_order: normalizeSectionOrder(
      o.section_order ?? o.sectionOrder,
    ),
  };
}
