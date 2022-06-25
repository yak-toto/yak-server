<template>
  <a v-on:click="getGroup" class="navbar-item">Groupe {{
      groupName
  }}</a>
</template>

<script>
export default {
  name: 'GroupButton',
  props: {
    groupName: String,
  },
  methods: {
    getGroup() {
      this.$router.push(`/groups/${this.groupName}`);
    },
  },
};
</script>
