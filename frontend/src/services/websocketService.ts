type WebSocketCallback = (event: any) => void;

class RealtimeWebSocketService {
  private socket: WebSocket | null = null;
  private listeners: Set<WebSocketCallback> = new Set();
  private reconnectInterval: number = 5000;
  private isExplicitlyClosed: boolean = false;

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isExplicitlyClosed = false;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/collaboration`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('[WebSocket] Real-time collaboration channel connected.');
      };

      this.socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          this.listeners.forEach((callback) => callback(parsed));
        } catch (err) {
          console.warn('[WebSocket] Message parse error:', err);
        }
      };

      this.socket.onclose = () => {
        if (!this.isExplicitlyClosed) {
          console.log(`[WebSocket] Closed. Attempting reconnect in ${this.reconnectInterval}ms...`);
          setTimeout(() => this.connect(), this.reconnectInterval);
        }
      };

      this.socket.onerror = (err) => {
        console.warn('[WebSocket] Error:', err);
      };
    } catch (e) {
      console.warn('[WebSocket] Connection failed:', e);
    }
  }

  subscribe(callback: WebSocketCallback) {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  send(type: string, payload: any, sender: string = 'User') {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, payload, sender, timestamp: new Date().toISOString() }));
    }
  }

  disconnect() {
    this.isExplicitlyClosed = true;
    if (this.socket) {
      this.socket.close();
    }
  }
}

export const realtimeService = new RealtimeWebSocketService();
