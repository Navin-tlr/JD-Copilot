import 'dart:convert';

class ChatMessage {
  final String role; // 'user' or 'assistant'
  final String content;
  final DateTime timestamp;
  final Map<String, dynamic>? metadata;

  ChatMessage({
    required this.role,
    required this.content,
    required this.timestamp,
    this.metadata,
  });

  Map<String, dynamic> toJson() => {
    'role': role,
    'content': content,
    'timestamp': timestamp.toIso8601String(),
    'metadata': metadata,
  };

  factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
    role: json['role'],
    content: json['content'],
    timestamp: DateTime.parse(json['timestamp']),
    metadata: json['metadata'],
  );
}

class ChatMemoryService {
  static const int _maxMessages = 50; // Keep last 50 messages for context
  
  List<ChatMessage> _messages = [];
  
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  
  // Get recent conversation context for LLM
  String getConversationContext() {
    if (_messages.isEmpty) return '';
    
    // Get last 10 messages for context
    final recentMessages = _messages.length > 10 
        ? _messages.sublist(_messages.length - 10) 
        : _messages;
    
    String context = 'Previous conversation context:\n';
    for (final message in recentMessages) {
      context += '${message.role.toUpperCase()}: ${message.content}\n';
    }
    context += '\nCurrent user query: ';
    
    return context;
  }
  
  // Add a new message to memory
  void addMessage(String role, String content, {Map<String, dynamic>? metadata}) {
    final message = ChatMessage(
      role: role,
      content: content,
      timestamp: DateTime.now(),
      metadata: metadata,
    );
    
    _messages.add(message);
    
    // Keep only last maxMessages
    if (_messages.length > _maxMessages) {
      _messages = _messages.sublist(_messages.length - _maxMessages);
    }
  }
  
  // Get conversation summary for LLM context
  String getConversationSummary() {
    if (_messages.isEmpty) return '';
    
    // Extract key information from recent messages
    final recentMessages = _messages.length > 5 
        ? _messages.sublist(_messages.length - 5) 
        : _messages;
    
    final userQueries = recentMessages
        .where((m) => m.role == 'user')
        .map((m) => m.content)
        .toList();
    
    if (userQueries.isEmpty) return '';
    
    String summary = 'Recent user queries: ';
    summary += userQueries.join('; ');
    summary += '\n\nProvide context-aware response based on this conversation history.';
    
    return summary;
  }
  
  // Clear conversation history
  void clearMemory() {
    _messages.clear();
  }
  
  // Get messages as JSON for storage
  String toJsonString() {
    return json.encode(_messages.map((m) => m.toJson()).toList());
  }
  
  // Load messages from JSON string
  void fromJsonString(String jsonString) {
    try {
      final List<dynamic> jsonList = json.decode(jsonString);
      _messages = jsonList.map((json) => ChatMessage.fromJson(json)).toList();
    } catch (e) {
      print('Error loading chat memory: $e');
      _messages = [];
    }
  }
}
