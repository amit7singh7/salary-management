const nf = (opts) => new Intl.NumberFormat("en-US", opts);

export const money = (n, currency = "USD") =>
  nf({ style: "currency", currency, maximumFractionDigits: 0 }).format(n);
export const usd = (n) => money(n, "USD");
export const compact = (n) => nf({ notation: "compact", maximumFractionDigits: 1 }).format(n);
export const count = (n) => nf({}).format(n);

export const TYPE_LABEL = { full_time: "Full-time", part_time: "Part-time", contract: "Contract" };
export const GROUP_LABEL = {
  country: "Country", department: "Department",
  job_title: "Job title", employment_type: "Employment type",
};
export const groupName = (field, value) => (field === "employment_type" ? TYPE_LABEL[value] || value : value);
