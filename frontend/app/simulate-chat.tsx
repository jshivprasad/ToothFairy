import React, { useState, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, FlatList, ActivityIndicator, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { colors, spacing, radius } from '../src/theme';

const c = colors.light;

interface ChatMessage {
  id: string;
  role: 'patient' | 'ai' | 'system';
  text: string;
  action?: string;
  timestamp: string;
}

export default function SimulateChatScreen() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'system',
      text: 'This simulates a real patient phone call to your clinic. The AI agent uses the SAME logic as real Twilio voice calls — same GPT-5.2 prompts, same appointment booking, same emergency handling.\n\nTry saying:\n• "Mujhe appointment chahiye"\n• "Clinic ka timing kya hai?"\n• "Emergency hai, dard ho raha hai"\n• "What are the fees?"',
      timestamp: new Date().toISOString(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const listRef = useRef<FlatList>(null);

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput('');

    const patientMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'patient',
      text,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, patientMsg]);
    setLoading(true);

    try {
      const res = await api.simulateCall({
        message: text,
        session_id: sessionId || undefined,
      });

      if (!sessionId && res.session_id) {
        setSessionId(res.session_id);
      }

      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        text: res.response,
        action: res.action,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, aiMsg]);

      // Show system message for special actions
      if (res.action === 'BOOK_APPOINTMENT') {
        setMessages(prev => [...prev, {
          id: (Date.now() + 2).toString(),
          role: 'system',
          text: '✅ Appointment booked! Check your Appointments tab. WhatsApp notification sent to doctor (if configured).',
          timestamp: new Date().toISOString(),
        }]);
      } else if (res.action === 'TRANSFER_TO_DOCTOR') {
        setMessages(prev => [...prev, {
          id: (Date.now() + 2).toString(),
          role: 'system',
          text: '📞 In a real call, this would transfer the patient to the doctor\'s phone number via Twilio <Dial>.',
          timestamp: new Date().toISOString(),
        }]);
      } else if (res.action === 'EMERGENCY_AFTER_HOURS') {
        setMessages(prev => [...prev, {
          id: (Date.now() + 2).toString(),
          role: 'system',
          text: '🚨 Emergency noted. In production, WhatsApp with patient details is sent to doctor for callback.',
          timestamp: new Date().toISOString(),
        }]);
      }
    } catch (e: any) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'system',
        text: `Error: ${e.message}`,
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }

  function resetChat() {
    setSessionId('');
    setMessages([{
      id: '0', role: 'system',
      text: 'New call simulation started. Say something to begin!',
      timestamp: new Date().toISOString(),
    }]);
  }

  const renderMessage = ({ item }: { item: ChatMessage }) => {
    if (item.role === 'system') {
      return (
        <View style={styles.systemMsg}>
          <Text style={styles.systemMsgText}>{item.text}</Text>
        </View>
      );
    }

    const isPatient = item.role === 'patient';
    return (
      <View style={[styles.msgRow, isPatient && styles.msgRowPatient]}>
        <View style={[styles.msgBubble, isPatient ? styles.patientBubble : styles.aiBubble]}>
          <View style={styles.msgHeader}>
            <Ionicons
              name={isPatient ? 'person' : 'pulse'}
              size={14}
              color={isPatient ? '#FFF' : c.primary}
            />
            <Text style={[styles.msgRole, isPatient && styles.msgRolePatient]}>
              {isPatient ? 'Patient' : 'AI Receptionist'}
            </Text>
          </View>
          <Text style={[styles.msgText, isPatient && styles.msgTextPatient]}>{item.text}</Text>
          {item.action && item.action !== 'CONTINUE' && (
            <View style={styles.actionBadge}>
              <Text style={styles.actionBadgeText}>{item.action}</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.flex} keyboardVerticalOffset={90}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <View style={styles.aiDot} />
            <View>
              <Text style={styles.headerTitle}>AI Call Simulation</Text>
              <Text style={styles.headerSub}>Test your AI receptionist</Text>
            </View>
          </View>
          <TouchableOpacity testID="reset-chat-btn" style={styles.resetBtn} onPress={resetChat}>
            <Ionicons name="refresh" size={20} color={c.primary} />
          </TouchableOpacity>
        </View>

        {/* Messages */}
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          contentContainerStyle={styles.messageList}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
        />

        {/* Input */}
        <View style={styles.inputBar}>
          <TextInput
            testID="chat-input"
            style={styles.chatInput}
            placeholder="Type as a patient calling..."
            placeholderTextColor={c.textMuted}
            value={input}
            onChangeText={setInput}
            onSubmitEditing={sendMessage}
            returnKeyType="send"
            editable={!loading}
          />
          <TouchableOpacity
            testID="send-message-btn"
            style={[styles.sendBtn, (!input.trim() || loading) && styles.sendBtnDisabled]}
            onPress={sendMessage}
            disabled={!input.trim() || loading}
          >
            {loading ? (
              <ActivityIndicator color="#FFF" size="small" />
            ) : (
              <Ionicons name="send" size={20} color="#FFF" />
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: c.background },
  flex: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: spacing.xl, paddingVertical: spacing.lg, backgroundColor: c.surface, borderBottomWidth: 1, borderBottomColor: c.border },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  aiDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#34D399' },
  headerTitle: { fontSize: 18, fontWeight: '600', color: c.textMain },
  headerSub: { fontSize: 13, color: c.textMuted },
  resetBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center' },
  messageList: { padding: spacing.lg, paddingBottom: spacing.xl },
  msgRow: { marginBottom: spacing.md, flexDirection: 'row' },
  msgRowPatient: { justifyContent: 'flex-end' },
  msgBubble: { maxWidth: '80%', borderRadius: radius.lg, padding: spacing.md },
  patientBubble: { backgroundColor: c.primary, borderBottomRightRadius: 4 },
  aiBubble: { backgroundColor: c.surface, borderWidth: 1, borderColor: c.border, borderBottomLeftRadius: 4 },
  msgHeader: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 4 },
  msgRole: { fontSize: 11, fontWeight: '600', color: c.textMuted },
  msgRolePatient: { color: 'rgba(255,255,255,0.7)' },
  msgText: { fontSize: 15, color: c.textMain, lineHeight: 22 },
  msgTextPatient: { color: '#FFF' },
  actionBadge: { marginTop: spacing.sm, backgroundColor: '#7C3AED15', borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 2, alignSelf: 'flex-start' },
  actionBadgeText: { fontSize: 11, color: '#7C3AED', fontWeight: '600' },
  systemMsg: { backgroundColor: '#F1F5F9', borderRadius: radius.md, padding: spacing.md, marginBottom: spacing.md },
  systemMsgText: { fontSize: 13, color: c.textMuted, lineHeight: 20 },
  inputBar: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, paddingVertical: spacing.md, backgroundColor: c.surface, borderTopWidth: 1, borderTopColor: c.border, gap: spacing.sm },
  chatInput: { flex: 1, backgroundColor: c.background, borderRadius: radius.full, paddingHorizontal: spacing.lg, paddingVertical: 12, fontSize: 16, color: c.textMain, borderWidth: 1, borderColor: c.border },
  sendBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: c.primary, alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled: { opacity: 0.5 },
});
