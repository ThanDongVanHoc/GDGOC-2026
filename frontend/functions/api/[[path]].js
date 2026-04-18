export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);
  
  // Cloudflare intercepts any request to /api/*
  // We forward it to the Azure VM public IP over HTTP.
  const targetHost = "http://20.41.123.4:8000";
  const targetUrl = targetHost + url.pathname + url.search;
  
  // Initialize headers
  const newHeaders = new Headers(request.headers);
  // Forward original IP
  newHeaders.set('X-Forwarded-For', request.headers.get('cf-connecting-ip') || '');

  // Create a new request based on the original
  const newRequest = new Request(targetUrl, {
    method: request.method,
    headers: newHeaders,
    body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : null,
    redirect: 'manual'
  });
  
  try {
    const response = await fetch(newRequest);
    
    // Copy the response to modify headers (add CORS so browser accepts it just in case)
    const newResponse = new Response(response.body, response);
    newResponse.headers.set('Access-Control-Allow-Origin', '*');
    newResponse.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    
    return newResponse;
  } catch (error) {
    return new Response(JSON.stringify({ error: "Cloudflare proxy could not reach Azure backend", details: error.message }), {
      status: 502,
      headers: { "Content-Type": "application/json" }
    });
  }
}
