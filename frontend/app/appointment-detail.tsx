import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../src/api';
import { colors, spacing, radius } from '../src/theme';

const c = colors.light;

export default function AppointmentDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [appointment, setAppointment] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) loadAppointment();
  }, [id]);

  async function loadAppointment() {
    try {
      const data = await api.getAppointment(id!);
      setAppointment(data);
    } catch (e) {
      console.log('Error:', e);
    } finally {
      setLoading(false);
    }
  }

  async function updateStatus(newStatus: string) {
    try {
      const updated = await api.updateAppointment(id!, { status: newStatus });
      setAppointment(updated);
      Alert.alert('Updated', `Appointment marked as ${newStatus}`);
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  }

  async function handleDelete() {
    Alert.alert('Delete Appointment', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete', style: 'destructive', onPress: async () => {
          try {
            await api.deleteAppointment(id!);
            router.back();
          } catch (e: any) {
            Alert.alert('Error', e.message);
          }
        }
      },
    ]);
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'confirmed': return c.success;
      case 'scheduled': return c.warning;
      case 'completed': return c.primary;
      case 'cancelled': return c.accent;
      default: return c.textMuted;
    }
  }

  if (loading) {
    return <View style={styles.loadingView}><ActivityIndicator size="large" color={c.primary} /></View>;
  }

  if (!appointment) {
    return (
      <View style={styles.loadingView}>
        <Text style={styles.errorText}>Appointment not found</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scroll}>
      {/* Status Banner */}
      <View style={[styles.statusBanner, { backgroundColor: getStatusColor(appointment.status) + '15' }]}>
        <View style={[styles.statusDot, { backgroundColor: getStatusColor(appointment.status) }]} />
        <Text style={[styles.statusLabel, { color: getStatusColor(appointment.status) }]}>
          {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
        </Text>
        {appointment.source === 'ai_agent' && (
          <View style={styles.aiBadge}>
            <Ionicons name="pulse" size={12} color="#7C3AED" />
            <Text style={styles.aiBadgeText}>AI Booked</Text>
          </View>
        )}
      </View>

      {/* Patient Info */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Patient Information</Text>
        <InfoRow icon="person" label="Name" value={appointment.patient_name} />
        <InfoRow icon="call" label="Phone" value={appointment.patient_phone} />
        {appointment.patient_email ? <InfoRow icon="mail" label="Email" value={appointment.patient_email} /> : null}
      </View>

      {/* Appointment Info */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Appointment Details</Text>
        <InfoRow icon="calendar" label="Date" value={appointment.preferred_date} />
        <InfoRow icon="time" label="Time" value={appointment.preferred_time} />
        <InfoRow icon="medical" label="Problem" value={appointment.problem_description || 'Not specified'} />
        {appointment.notes ? <InfoRow icon="document-text" label="Notes" value={appointment.notes} /> : null}
      </View>

      {/* Status Actions */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Update Status</Text>
        <View style={styles.statusActions}>
          {['scheduled', 'confirmed', 'completed', 'cancelled'].map(s => (
            <TouchableOpacity
              key={s}
              testID={`status-${s}-btn`}
              style={[styles.statusBtn, appointment.status === s && { backgroundColor: getStatusColor(s), borderColor: getStatusColor(s) }]}
              onPress={() => updateStatus(s)}
            >
              <Text style={[styles.statusBtnText, appointment.status === s && { color: '#FFF' }]}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Delete */}
      <TouchableOpacity testID="delete-appointment-btn" style={styles.deleteBtn} onPress={handleDelete}>
        <Ionicons name="trash-outline" size={20} color={c.accent} />
        <Text style={styles.deleteBtnText}>Delete Appointment</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function InfoRow({ icon, label, value }: any) {
  return (
    <View style={styles.infoRow}>
      <Ionicons name={icon} size={18} color={c.textMuted} />
      <View style={styles.infoContent}>
        <Text style={styles.infoLabel}>{label}</Text>
        <Text style={styles.infoValue}>{value}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: c.background },
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: c.background },
  errorText: { fontSize: 16, color: c.textMuted },
  scroll: { padding: spacing.xl, paddingBottom: 100 },
  statusBanner: { flexDirection: 'row', alignItems: 'center', borderRadius: radius.lg, padding: spacing.lg, marginBottom: spacing.xl },
  statusDot: { width: 10, height: 10, borderRadius: 5, marginRight: spacing.md },
  statusLabel: { fontSize: 18, fontWeight: '600', flex: 1 },
  aiBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#7C3AED15', borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 4, gap: 4 },
  aiBadgeText: { fontSize: 12, color: '#7C3AED', fontWeight: '600' },
  card: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, marginBottom: spacing.lg, borderWidth: 1, borderColor: c.border },
  cardTitle: { fontSize: 16, fontWeight: '600', color: c.textMain, marginBottom: spacing.lg },
  infoRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: spacing.lg, gap: spacing.md },
  infoContent: { flex: 1 },
  infoLabel: { fontSize: 12, color: c.textMuted, marginBottom: 2 },
  infoValue: { fontSize: 16, color: c.textMain, fontWeight: '500' },
  statusActions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  statusBtn: { paddingHorizontal: spacing.lg, paddingVertical: spacing.sm, borderRadius: radius.full, borderWidth: 1, borderColor: c.border },
  statusBtnText: { fontSize: 14, fontWeight: '500', color: c.textMain },
  deleteBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: spacing.lg, gap: spacing.sm, marginTop: spacing.lg },
  deleteBtnText: { fontSize: 16, color: c.accent, fontWeight: '500' },
});
