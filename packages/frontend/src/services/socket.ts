import { io, Socket } from 'socket.io-client';
import { SocketEvents } from '@/types';

class SocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();

  connect(token?: string): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    const socketUrl = import.meta.env.VITE_SOCKET_URL || window.location.origin;
    
    this.socket = io(socketUrl, {
      auth: {
        token: token || localStorage.getItem('auth-token'),
      },
      transports: ['websocket', 'polling'],
      timeout: 20000,
      retries: 3,
    });

    this.setupEventHandlers();
    return this.socket;
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.listeners.clear();
    }
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('Socket connected:', this.socket?.id);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
    });

    this.socket.on('error', (error) => {
      console.error('Socket error:', error);
    });

    // Handle reconnection
    this.socket.on('reconnect', (attemptNumber) => {
      console.log('Socket reconnected after', attemptNumber, 'attempts');
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('Socket reconnection error:', error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('Socket reconnection failed');
    });
  }

  // Subscribe to a specific event
  on<K extends keyof SocketEvents>(event: K, callback: SocketEvents[K]): void {
    if (!this.socket) {
      console.warn('Socket not connected. Call connect() first.');
      return;
    }

    this.socket.on(event, callback as any);

    // Track listeners for cleanup
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  // Unsubscribe from a specific event
  off<K extends keyof SocketEvents>(event: K, callback?: SocketEvents[K]): void {
    if (!this.socket) return;

    if (callback) {
      this.socket.off(event, callback as any);
      this.listeners.get(event)?.delete(callback);
    } else {
      this.socket.off(event);
      this.listeners.delete(event);
    }
  }

  // Emit an event to the server
  emit(event: string, data?: any): void {
    if (!this.socket?.connected) {
      console.warn('Socket not connected. Cannot emit event:', event);
      return;
    }

    this.socket.emit(event, data);
  }

  // Check if socket is connected
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Get socket instance
  getSocket(): Socket | null {
    return this.socket;
  }

  // Join a room (for document-specific updates)
  joinRoom(room: string): void {
    this.emit('join', room);
  }

  // Leave a room
  leaveRoom(room: string): void {
    this.emit('leave', room);
  }

  // Subscribe to document updates
  subscribeToDocument(documentId: string, callbacks: {
    onUpdate?: (document: any) => void;
    onProgress?: (data: { id: string; progress: number }) => void;
    onCompleted?: (document: any) => void;
    onError?: (data: { id: string; error: string }) => void;
  }): void {
    this.joinRoom(`document:${documentId}`);

    if (callbacks.onUpdate) {
      this.on('document:updated', callbacks.onUpdate);
    }
    if (callbacks.onProgress) {
      this.on('document:processing', callbacks.onProgress);
    }
    if (callbacks.onCompleted) {
      this.on('document:completed', callbacks.onCompleted);
    }
    if (callbacks.onError) {
      this.on('document:error', callbacks.onError);
    }
  }

  // Unsubscribe from document updates
  unsubscribeFromDocument(documentId: string, callbacks?: {
    onUpdate?: (document: any) => void;
    onProgress?: (data: { id: string; progress: number }) => void;
    onCompleted?: (document: any) => void;
    onError?: (data: { id: string; error: string }) => void;
  }): void {
    this.leaveRoom(`document:${documentId}`);

    if (callbacks) {
      if (callbacks.onUpdate) {
        this.off('document:updated', callbacks.onUpdate);
      }
      if (callbacks.onProgress) {
        this.off('document:processing', callbacks.onProgress);
      }
      if (callbacks.onCompleted) {
        this.off('document:completed', callbacks.onCompleted);
      }
      if (callbacks.onError) {
        this.off('document:error', callbacks.onError);
      }
    } else {
      // Remove all listeners for document events
      this.off('document:updated');
      this.off('document:processing');
      this.off('document:completed');
      this.off('document:error');
    }
  }

  // Subscribe to user presence updates
  subscribeToUserPresence(callbacks: {
    onUserConnected?: (data: { userId: string; count: number }) => void;
    onUserDisconnected?: (data: { userId: string; count: number }) => void;
  }): void {
    if (callbacks.onUserConnected) {
      this.on('user:connected', callbacks.onUserConnected);
    }
    if (callbacks.onUserDisconnected) {
      this.on('user:disconnected', callbacks.onUserDisconnected);
    }
  }

  // Unsubscribe from user presence updates
  unsubscribeFromUserPresence(callbacks?: {
    onUserConnected?: (data: { userId: string; count: number }) => void;
    onUserDisconnected?: (data: { userId: string; count: number }) => void;
  }): void {
    if (callbacks) {
      if (callbacks.onUserConnected) {
        this.off('user:connected', callbacks.onUserConnected);
      }
      if (callbacks.onUserDisconnected) {
        this.off('user:disconnected', callbacks.onUserDisconnected);
      }
    } else {
      this.off('user:connected');
      this.off('user:disconnected');
    }
  }

  // Ping the server
  ping(callback?: (latency: number) => void): void {
    if (!this.socket?.connected) return;

    const start = Date.now();
    this.socket.emit('ping', start, (acknowledgment: number) => {
      const latency = Date.now() - start;
      if (callback) {
        callback(latency);
      }
    });
  }

  // Request server status
  getServerStatus(callback: (status: any) => void): void {
    if (!this.socket?.connected) return;

    this.socket.emit('server:status', callback);
  }

  // Clean up all listeners and disconnect
  cleanup(): void {
    this.listeners.clear();
    this.disconnect();
  }
}

export const socketService = new SocketService();
export default socketService;

