import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { colors, spacing, radius } from '../src/theme';

const c = colors.light;

export default function AddAppointmentScreen() {
  const router = useRouter();
  const [form, setForm] = useState({
    patient_name: '',
    patient_phone: '',
    patient_email: '',
    problem_description: '',
    preferred_date: new Date().toISOString().split('T')[0],
    preferred_time: '10:00',
    notes: '',
  });
  const [loading, setLoading] = useState(false);

  async function handleCreate() {
    if (!form.patient_name.trim() || !form.patient_phone.trim()) {
      Alert.alert('Error', 'Patient name and phone are required');
      return;
    }
    setLoading(true);
    try {
      await api.createAppointment(form);
      Alert.alert('Success', 'Appointment created successfully', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (e: any) {
      Alert.alert('Error', e.message || 'Failed to create appointment');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.flex}>
      <ScrollView style={styles.container} contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Patient Details</Text>

          <Text style={styles.label}>Name *</Text>
          <TextInput testID="appt-patient-name" style={styles.input} placeholder="Patient name" placeholderTextColor={c.textMuted} value={form.patient_name} onChangeText={(v) => setForm({ ...form, patient_name: v })} />

          <Text style={styles.label}>Phone *</Text>
          <TextInput testID="appt-patient-phone" style={styles.input} placeholder="+919876543210" placeholderTextColor={c.textMuted} value={form.patient_phone} onChangeText={(v) => setForm({ ...form, patient_phone: v })} keyboardType="phone-pad" />

          <Text style={styles.label}>Email</Text>
          <TextInput testID="appt-patient-email" style={styles.input} placeholder="patient@email.com" placeholderTextColor={c.textMuted} value={form.patient_email} onChangeText={(v) => setForm({ ...form, patient_email: v })} keyboardType="email-address" autoCapitalize="none" />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Appointment Details</Text>

          <Text style={styles.label}>Problem / Treatment</Text>
          <TextInput testID="appt-problem" style={[styles.input, styles.multiline]} placeholder="Describe the dental issue..." placeholderTextColor={c.textMuted} value={form.problem_description} onChangeText={(v) => setForm({ ...form, problem_description: v })} multiline numberOfLines={3} />

          <Text style={styles.label}>Preferred Date</Text>
          <TextInput testID="appt-date" style={styles.input} placeholder="YYYY-MM-DD" placeholderTextColor={c.textMuted} value={form.preferred_date} onChangeText={(v) => setForm({ ...form, preferred_date: v })} />

          <Text style={styles.label}>Preferred Time</Text>
          <View style={styles.timeRow}>
            {['09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00'].map(t => (
              <TouchableOpacity
                key={t}
                testID={`time-${t}`}
                style={[styles.timeChip, form.preferred_time === t && styles.timeChipActive]}
                onPress={() => setForm({ ...form, preferred_time: t })}
              >
                <Text style={[styles.timeChipText, form.preferred_time === t && styles.timeChipTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Notes</Text>
          <TextInput testID="appt-notes" style={[styles.input, styles.multiline]} placeholder="Additional notes..." placeholderTextColor={c.textMuted} value={form.notes} onChangeText={(v) => setForm({ ...form, notes: v })} multiline numberOfLines={2} />
        </View>

        <TouchableOpacity testID="create-appointment-btn" style={styles.createBtn} onPress={handleCreate} disabled={loading} activeOpacity={0.8}>
          {loading ? <ActivityIndicator color="#FFF" /> : (
            <View style={styles.createBtnContent}>
              <Ionicons name="calendar" size={20} color="#FFF" />
              <Text style={styles.createBtnText}>Book Appointment</Text>
            </View>
          )}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: c.background },
  container: { flex: 1 },
  scroll: { padding: spacing.xl, paddingBottom: 100 },
  section: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, marginBottom: spacing.xl, borderWidth: 1, borderColor: c.border },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: c.textMain, marginBottom: spacing.lg },
  label: { fontSize: 13, fontWeight: '500', color: c.textMuted, marginBottom: spacing.xs, marginTop: spacing.md },
  input: { backgroundColor: c.background, borderRadius: radius.md, borderWidth: 1, borderColor: c.border, paddingHorizontal: spacing.md, paddingVertical: 12, fontSize: 16, color: c.textMain },
  multiline: { minHeight: 80, textAlignVertical: 'top' },
  timeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.sm },
  timeChip: { paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, borderRadius: radius.full, borderWidth: 1, borderColor: c.border, backgroundColor: c.surface },
  timeChipActive: { backgroundColor: c.primary, borderColor: c.primary },
  timeChipText: { fontSize: 14, color: c.textMuted, fontWeight: '500' },
  timeChipTextActive: { color: '#FFF' },
  createBtn: { backgroundColor: c.primary, borderRadius: radius.full, paddingVertical: 16, alignItems: 'center' },
  createBtnContent: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  createBtnText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
});
