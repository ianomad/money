import { handleAdminRequest } from "../_lib/admin/handlers.js";

export async function onRequest(context) {
  return handleAdminRequest(context.request, context.env);
}
