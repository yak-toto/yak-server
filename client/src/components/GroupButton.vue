<template>
  <a v-on:click="getGroup" class="navbar-item">{{ groupDescription }}</a>
</template>

<script>
export default {
  name: 'GroupButton',
  props: {
    groupName: String,
    groupDescription: String,
  },
  methods: {
    getGroup() {
      this.$router.push(`/groups/${this.groupName}`);
    },
  },
};
</script>
