<template>
  <div>{{ group_name }}</div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'GroupView',
  props: {
    group_name: String,
  },
  data() {
    return {
      group_resource: [],
    };
  },
  methods: {
    getGroup() {
      const path = `http://localhost:5000/groups/${this.group_name}`;
      axios.get(path)
        .then((res) => {
          this.group_resource = res.data.group_resource;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
  },
  created() {
    this.getGroup();
  },
};

</script>
