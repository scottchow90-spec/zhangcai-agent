// The local bridge response is validated at runtime; this narrows the browser API
// for the small client call without weakening the rest of the application types.
interface Response {
  json(): Promise<any>;
}
