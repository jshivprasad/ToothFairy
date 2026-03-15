import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator, Alert, Switch } from 'react-native';
import { useRouter } from 'expo-router';
import { api } from '../src/api';
import { colors, spacing, radius } from '../src/theme';

const c = colors.light;

export default function ClinicHoursScreen() {
  const router = useRouter();
  const [hours, setHours] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadHours(); }, []);

  async function loadHours() {
    try {
      const data = await api.getClinicHours();
      setHours(data);
    } catch (e) {
      console.log('Error loading hours:', e);
    } finally {
      setLoading(false);
    }
  }

  function updateDay(index: number, field: string, value: any) {
    const updated = [...hours];
    updated[index] = { ...updated[index], [field]: value };
    setHours(updated);
  }

  async function handleSave() {
    setSaving(true);
    try {
      await api.updateClinicHours({
        hours: hours.map(h => ({
          day: h.day,
          is_open: h.is_open,
          open_time: h.open_time,
          close_time: h.close_time,
          break_start: h.break_start,
          break_end: h.break_end,
        }))
      });
      Alert.alert('Success', 'Clinic hours updated. AI agent will reflect these changes.');
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
    <ScrollView style={styles.container} contentContainerStyle={styles.scroll}>
      <Text style={styles.hint}>Set your clinic operating hours. The AI agent will use these to inform patients and handle calls accordingly.</Text>

      {hours.map((h, i) => (
        <View key={h.day} style={[styles.dayCard, !h.is_open && styles.dayCardClosed]}>
          <View style={styles.dayHeader}>
            <Text style={styles.dayName}>{h.day}</Text>
            <Switch
              testID={`toggle-${h.day}`}
              value={h.is_open}
              onValueChange={(v) => updateDay(i, 'is_open', v)}
              trackColor={{ false: c.border, true: c.primary + '40' }}
              thumbColor={h.is_open ? c.primary : '#CCC'}
            />
          </View>
          {h.is_open && (
            <View style={styles.timesRow}>
              <TimeBlock label="Open" value={h.open_time} onChange={(v: string) => updateDay(i, 'open_time', v)} testID={`open-${h.day}`} />
              <TimeBlock label="Close" value={h.close_time} onChange={(v: string) => updateDay(i, 'close_time', v)} testID={`close-${h.day}`} />
              <TimeBlock label="Break Start" value={h.break_start} onChange={(v: string) => updateDay(i, 'break_start', v)} testID={`break-start-${h.day}`} />
              <TimeBlock label="Break End" value={h.break_end} onChange={(v: string) => updateDay(i, 'break_end', v)} testID={`break-end-${h.day}`} />
            </View>
          )}
          {!h.is_open && (
            <Text style={styles.closedText}>Closed</Text>
          )}
        </View>
      ))}

      <TouchableOpacity testID="save-hours-btn" style={styles.saveBtn} onPress={handleSave} disabled={saving} activeOpacity={0.8}>
        {saving ? <ActivityIndicator color="#FFF" /> : <Text style={styles.saveBtnText}>Save Hours</Text>}
      </TouchableOpacity>
    </ScrollView>
  );
}

function TimeBlock({ label, value, onChange, testID }: any) {
  const times = [];
  for (let h = 0; h < 24; h++) {
    for (let m = 0; m < 60; m += 30) {
      times.push(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`);
    }
  }
  const currentIndex = times.indexOf(value);

  function cycle() {
    const nextIndex = (currentIndex + 1) % times.length;
    onChange(times[nextIndex]);
  }

  return (
    <View style={styles.timeBlock}>
      <Text style={styles.timeLabel}>{label}</Text>
      <TouchableOpacity testID={testID} style={styles.timeValue} onPress={cycle}>
        <Text style={styles.timeText}>{value}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: c.background },
  loadingView: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: c.background },
  scroll: { padding: spacing.xl, paddingBottom: 100 },
  hint: { fontSize: 14, color: c.textMuted, marginBottom: spacing.xl, lineHeight: 20 },
  dayCard: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.lg, marginBottom: spacing.md, borderWidth: 1, borderColor: c.border },
  dayCardClosed: { opacity: 0.6 },
  dayHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  dayName: { fontSize: 18, fontWeight: '600', color: c.textMain },
  timesRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, marginTop: spacing.lg },
  timeBlock: { width: '46%' },
  timeLabel: { fontSize: 12, color: c.textMuted, marginBottom: spacing.xs },
  timeValue: { backgroundColor: c.background, borderRadius: radius.md, borderWidth: 1, borderColor: c.border, paddingVertical: 10, paddingHorizontal: spacing.md, alignItems: 'center' },
  timeText: { fontSize: 16, fontWeight: '600', color: c.primary },
  closedText: { fontSize: 14, color: c.accent, marginTop: spacing.sm, fontWeight: '500' },
  saveBtn: { backgroundColor: c.primary, borderRadius: radius.full, paddingVertical: 16, alignItems: 'center', marginTop: spacing.xl },
  saveBtnText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
});
