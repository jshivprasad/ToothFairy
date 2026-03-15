import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert, Switch, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { colors, spacing, radius } from '../src/theme';

const c = colors.light;

export default function AIConfigScreen() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadConfig(); }, []);

  async function loadConfig() {
    try {
      const data = await api.getAIConfig();
      setConfig(data);
    } catch (e) {
      console.log('Error:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      await api.updateAIConfig({
        is_active: config.is_active,
        greeting_message: config.greeting_message,
        language_preference: config.language_preference,
        forward_to_doctor: config.forward_to_doctor,
        collect_patient_info: config.collect_patient_info,
        book_appointments: config.book_appointments,
        emergency_handling: config.emergency_handling,
        doctor_whatsapp: config.doctor_whatsapp,
        staff_whatsapp: config.staff_whatsapp,
      });
      Alert.alert('Success', 'AI Agent configuration updated');
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <View style={styles.loadingView}><ActivityIndicator size="large" color={c.primary} /></View>;
  }

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1, backgroundColor: c.background }}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        {/* Status Card */}
        <View style={[styles.statusCard, config.is_active && styles.statusCardActive]}>
          <View style={styles.statusContent}>
            <Ionicons name="pulse" size={28} color={config.is_active ? '#FFF' : c.textMuted} />
            <View style={styles.statusTextWrap}>
              <Text style={[styles.statusTitle, config.is_active && styles.statusTitleActive]}>
                AI Receptionist
              </Text>
              <Text style={[styles.statusSub, config.is_active && styles.statusSubActive]}>
                {config.is_active ? 'Active - Receiving patient calls' : 'Inactive'}
              </Text>
            </View>
          </View>
          <Switch
            testID="ai-active-toggle"
            value={config.is_active}
            onValueChange={(v) => setConfig({ ...config, is_active: v })}
            trackColor={{ false: c.border, true: '#34D39960' }}
            thumbColor={config.is_active ? '#34D399' : '#CCC'}
          />
        </View>

        {/* Greeting Message */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Greeting Message</Text>
          <TextInput
            testID="greeting-input"
            style={[styles.input, styles.multiline]}
            value={config.greeting_message}
            onChangeText={(v) => setConfig({ ...config, greeting_message: v })}
            multiline
            numberOfLines={3}
          />
        </View>

        {/* Language */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Language Preference</Text>
          <View style={styles.langRow}>
            {['hindi', 'english', 'marathi'].map(lang => (
              <TouchableOpacity
                key={lang}
                testID={`lang-${lang}`}
                style={[styles.langChip, config.language_preference === lang && styles.langChipActive]}
                onPress={() => setConfig({ ...config, language_preference: lang })}
              >
                <Text style={[styles.langText, config.language_preference === lang && styles.langTextActive]}>
                  {lang.charAt(0).toUpperCase() + lang.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.hint}>Default language for AI agent. It can switch based on patient's preference.</Text>
        </View>

        {/* Capabilities */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Capabilities</Text>
          <ToggleRow testID="toggle-forward" label="Forward calls to doctor during clinic hours" value={config.forward_to_doctor} onChange={(v: boolean) => setConfig({ ...config, forward_to_doctor: v })} />
          <ToggleRow testID="toggle-collect-info" label="Collect patient information" value={config.collect_patient_info} onChange={(v: boolean) => setConfig({ ...config, collect_patient_info: v })} />
          <ToggleRow testID="toggle-book-appts" label="Book appointments automatically" value={config.book_appointments} onChange={(v: boolean) => setConfig({ ...config, book_appointments: v })} />
          <ToggleRow testID="toggle-emergency" label="Handle emergency calls" value={config.emergency_handling} onChange={(v: boolean) => setConfig({ ...config, emergency_handling: v })} />
        </View>

        {/* WhatsApp Numbers */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>WhatsApp Notifications</Text>
          <Text style={styles.label}>Doctor WhatsApp</Text>
          <TextInput testID="doctor-whatsapp-input" style={styles.input} value={config.doctor_whatsapp} onChangeText={(v) => setConfig({ ...config, doctor_whatsapp: v })} keyboardType="phone-pad" placeholder="+919876543210" placeholderTextColor={c.textMuted} />
          <Text style={styles.label}>Staff WhatsApp</Text>
          <TextInput testID="staff-whatsapp-input" style={styles.input} value={config.staff_whatsapp} onChangeText={(v) => setConfig({ ...config, staff_whatsapp: v })} keyboardType="phone-pad" placeholder="+919876543210" placeholderTextColor={c.textMuted} />
        </View>

        <TouchableOpacity testID="save-ai-config-btn" style={styles.saveBtn} onPress={handleSave} disabled={saving} activeOpacity={0.8}>
          {saving ? <ActivityIndicator color="#FFF" /> : <Text style={styles.saveBtnText}>Save Configuration</Text>}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function ToggleRow({ testID, label, value, onChange }: any) {
  return (
    <View style={styles.toggleRow}>
      <Text style={styles.toggleLabel}>{label}</Text>
      <Switch
        testID={testID}
        value={value}
        onValueChange={onChange}
        trackColor={{ false: c.border, true: c.primary + '40' }}
        thumbColor={value ? c.primary : '#CCC'}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: c.background },
  scroll: { padding: spacing.xl, paddingBottom: 100 },
  statusCard: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, marginBottom: spacing.xl, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1, borderColor: c.border },
  statusCardActive: { backgroundColor: '#7C3AED', borderColor: '#7C3AED' },
  statusContent: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  statusTextWrap: { marginLeft: spacing.md },
  statusTitle: { fontSize: 18, fontWeight: '600', color: c.textMain },
  statusTitleActive: { color: '#FFF' },
  statusSub: { fontSize: 13, color: c.textMuted, marginTop: 2 },
  statusSubActive: { color: 'rgba(255,255,255,0.8)' },
  section: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, marginBottom: spacing.lg, borderWidth: 1, borderColor: c.border },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: c.textMain, marginBottom: spacing.lg },
  input: { backgroundColor: c.background, borderRadius: radius.md, borderWidth: 1, borderColor: c.border, paddingHorizontal: spacing.md, paddingVertical: 12, fontSize: 16, color: c.textMain },
  multiline: { minHeight: 80, textAlignVertical: 'top' },
  label: { fontSize: 13, fontWeight: '500', color: c.textMuted, marginBottom: spacing.xs, marginTop: spacing.md },
  hint: { fontSize: 12, color: c.textMuted, marginTop: spacing.md, lineHeight: 18 },
  langRow: { flexDirection: 'row', gap: spacing.sm },
  langChip: { paddingHorizontal: spacing.xl, paddingVertical: spacing.md, borderRadius: radius.full, borderWidth: 1, borderColor: c.border },
  langChipActive: { backgroundColor: c.primary, borderColor: c.primary },
  langText: { fontSize: 14, fontWeight: '500', color: c.textMain },
  langTextActive: { color: '#FFF' },
  toggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: c.border },
  toggleLabel: { flex: 1, fontSize: 15, color: c.textMain, marginRight: spacing.md },
  saveBtn: { backgroundColor: c.primary, borderRadius: radius.full, paddingVertical: 16, alignItems: 'center', marginTop: spacing.lg },
  saveBtnText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
});
