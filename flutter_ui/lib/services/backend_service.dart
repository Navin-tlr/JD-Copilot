import 'dart:convert';
import 'package:http/http.dart' as http;

import 'dart:io';
import 'package:flutter/foundation.dart';

class BackendService {
  // Use different URLs based on platform
  static String get _baseUrl {
    if (kIsWeb) {
      // For web, use localhost instead of 127.0.0.1
      return 'http://localhost:8000';
    } else if (Platform.isAndroid) {
      // For Android emulator, use 10.0.2.2 (special IP for host machine)
      return 'http://10.0.2.2:8000';
    } else {
      // For iOS simulator and desktop, use localhost
      return 'http://localhost:8000';
    }
  }
  
  // Headers for all requests
  static const Map<String, String> _headers = {
    'Content-Type': 'application/json',
  };

  // Health check
  static Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/health'),
        headers: _headers,
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Health check failed: $e');
      return false;
    }
  }

  // Main query endpoint
  static Future<Map<String, dynamic>> query({
    required String question,
    String? company,
    int? year,
    String? roleContains,
    int topK = 3,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/query'),
        headers: _headers,
        body: json.encode({
          'question': question,
          'top_k': topK,
          'filters': {
            'company': company,
            'year': year,
            'role_contains': roleContains,
          },
        }),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Query failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Query error: $e');
    }
  }

  // Get companies list
  static Future<List<String>> getCompanies() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/companies'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return List<String>.from(data['companies'] ?? []);
      } else {
        throw Exception('Failed to get companies: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Companies error: $e');
    }
  }

  // Get placement statistics
  static Future<Map<String, dynamic>> getPlacementStats() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/stats/placement'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Stats failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Stats error: $e');
    }
  }

  // Get company statistics
  static Future<Map<String, dynamic>> getCompanyStats() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/stats/companies'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Company stats failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Company stats error: $e');
    }
  }

  // Search skills
  static Future<List<String>> searchSkills(String query) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/search/skills?skill=$query'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return List<String>.from(data['skills'] ?? []);
      } else {
        throw Exception('Skills search failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Skills search error: $e');
    }
  }

  // Get specialization insights
  static Future<Map<String, dynamic>> getSpecializationInsights() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/specialization/insights'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Specialization insights failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Specialization insights error: $e');
    }
  }

  // Resume matching
  static Future<Map<String, dynamic>> matchResume(String resumeText) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/query/resume_match'),
        headers: _headers,
        body: json.encode({
          'resume_text': resumeText,
          'top_k': 3,
        }),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Resume matching failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Resume matching error: $e');
    }
  }

  // GD simulation
  static Future<Map<String, dynamic>> simulateGD(String transcript) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/gd/simulate'),
        headers: _headers,
        body: json.encode({
          'transcript': transcript,
        }),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('GD simulation failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('GD simulation error: $e');
    }
  }

  // Get alerts
  static Future<List<Map<String, dynamic>>> getAlerts() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/alerts'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return List<Map<String, dynamic>>.from(data['alerts'] ?? []);
      } else {
        throw Exception('Alerts failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Alerts error: $e');
    }
  }
}
