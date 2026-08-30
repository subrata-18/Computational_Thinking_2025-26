const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL ?? "").trim().replace(/\/$/, "");
const supabaseKey = (import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? "").trim();
export const SUPABASE_BUCKET = (import.meta.env.VITE_SUPABASE_BUCKET ?? "Images").trim();

if (!supabaseUrl || !supabaseKey) {
  console.warn(
    "Nova AI: Supabase browser configuration is missing. Image uploads will be unavailable until VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY are configured.",
  );
}

export async function uploadQuestionImage(file: File): Promise<string> {
  if (!supabaseUrl || !supabaseKey) {
    throw new Error("Image upload is not configured. Please add the Supabase browser credentials to the frontend environment.");
  }

  const extension = file.name.split(".").pop()?.toLowerCase() ?? "png";
  const filename = `${crypto.randomUUID()}.${extension}`;
  const uploadUrl = `${supabaseUrl}/storage/v1/object/${encodeURIComponent(SUPABASE_BUCKET)}/${encodeURIComponent(filename)}`;

  let response: Response;
  try {
    response = await fetch(uploadUrl, {
      method: "POST",
      headers: {
        apikey: supabaseKey,
        Authorization: `Bearer ${supabaseKey}`,
        "Content-Type": file.type,
        "x-upsert": "false",
      },
      body: file,
    });
  } catch {
    throw new Error("Unable to connect to Supabase. Please try again.");
  }

  if (!response.ok) {
    throw new Error("Image upload failed. Please try again.");
  }

  // The object was uploaded to the root of the configured bucket, so the
  // path expected by the Flask server is the generated filename itself.


  return filename;
}
